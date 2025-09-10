import json
import logging
import os
import shutil
from collections.abc import Callable
from json import JSONDecodeError
from pathlib import Path
from threading import Event
from typing import Any

import tidalapi
from requests import HTTPError

from tidal_dl_ng.helper.decorator import SingletonMeta
from tidal_dl_ng.helper.path import path_config_base, path_file_settings, path_file_token
from tidal_dl_ng.model.cfg import Settings as ModelSettings
from tidal_dl_ng.model.cfg import Token as ModelToken
from tidal_dl_ng.network import NetworkManager, ProxyConnectionError, NetworkTimeoutError, ProxyAuthenticationError


logger = logging.getLogger(__name__)


class BaseConfig:
    data: ModelSettings | ModelToken
    file_path: str
    cls_model: ModelSettings | ModelToken
    path_base: str = path_config_base()

    def save(self, config_to_compare: str = None) -> None:
        data_json = self.data.to_json()

        # If old and current config is equal, skip the write operation.
        if config_to_compare == data_json:
            return

        # Try to create the base folder.
        os.makedirs(self.path_base, exist_ok=True)

        with open(self.file_path, encoding="utf-8", mode="w") as f:
            # Save it in a pretty format
            obj_json_config = json.loads(data_json)
            json.dump(obj_json_config, f, indent=4)

    def set_option(self, key: str, value: Any) -> None:
        value_old: Any = getattr(self.data, key)

        if type(value_old) == bool:  # noqa: E721
            value = True if value.lower() in ("true", "1", "yes", "y") else False  # noqa: SIM210
        elif type(value_old) == int and type(value) != int:  # noqa: E721
            value = int(value)

        setattr(self.data, key, value)

    def read(self, path: str) -> bool:
        result: bool = False
        settings_json: str = ""

        try:
            with open(path, encoding="utf-8") as f:
                settings_json = f.read()

            self.data = self.cls_model.from_json(settings_json)
            result = True
        except (JSONDecodeError, TypeError, FileNotFoundError, ValueError) as e:
            if isinstance(e, ValueError):
                path_bak = path + ".bak"

                # First check if a backup file already exists. If yes, remove it.
                if os.path.exists(path_bak):
                    os.remove(path_bak)

                # Move the invalid config file to the backup location.
                shutil.move(path, path_bak)
                # TODO: Implement better global logger.
                print(
                    "Something is wrong with your config. Maybe it is not compatible anymore due to a new app version."
                    f" You can find a backup of your old config here: '{path_bak}'. A new default config was created."
                )

            self.data = self.cls_model()

        # Call save in case of we need to update the saved config, due to changes in code.
        self.save(settings_json)

        return result


class Settings(BaseConfig, metaclass=SingletonMeta):
    def __init__(self):
        self.cls_model = ModelSettings
        self.file_path = path_file_settings()
        self.read(self.file_path)
        self._configure_network_manager()
    
    def _configure_network_manager(self) -> None:
        """Configure NetworkManager with current settings."""
        try:
            network_manager = NetworkManager()
            network_manager.configure(
                network_settings=self.data.network_settings,
                proxy_settings=self.data.proxy_settings
            )
        except Exception as e:
            # TODO: Use proper logger when available
            print(f"Warning: Failed to configure NetworkManager: {e}")
    
    def save(self, config_to_compare: str = None) -> None:
        """Override save to reconfigure NetworkManager after saving."""
        super().save(config_to_compare)
        self._configure_network_manager()


class Tidal(BaseConfig, metaclass=SingletonMeta):
    session: tidalapi.Session
    token_from_storage: bool = False
    settings: Settings
    is_pkce: bool
    _original_request_session: Any = None

    def __init__(self, settings: Settings = None):
        self.cls_model = ModelToken
        tidal_config: tidalapi.Config = tidalapi.Config(item_limit=10000)
        self.session = tidalapi.Session(tidal_config)
        # self.session.config.client_id = "km8T1xS355y7dd3H"
        # self.session.config.client_secret = "vcmeGW1OuZ0fWYMCSZ6vNvSLJlT3XEpW0ambgYt5ZuI="
        self.file_path = path_file_token()
        self.token_from_storage = self.read(self.file_path)

        # Store original session for monitoring
        self._original_request_session = self.session.request_session
        
        # Inject NetworkManager session
        self._inject_network_manager()

        if settings:
            self.settings = settings
            self.settings_apply()

    def _inject_network_manager(self) -> None:
        """Replace tidalapi's session with our NetworkManager session."""
        try:
            network_manager = NetworkManager()
            if network_manager.is_configured():
                # Replace tidalapi's request_session with our configured session
                self.session.request_session = network_manager.get_session("auth")
                logger.info("NetworkManager session injected into tidalapi")
            else:
                logger.warning("NetworkManager not configured, using default tidalapi session")
        except Exception as e:
            logger.error(f"Failed to inject NetworkManager session: {e}")
            # Continue with original session rather than failing

    def _monitor_session_integrity(self) -> None:
        """Check if tidalapi recreated the session and re-inject if needed."""
        try:
            network_manager = NetworkManager()
            if (network_manager.is_configured() and 
                self.session.request_session != network_manager.get_session("auth")):
                logger.warning("tidalapi session was recreated, re-injecting NetworkManager")
                self._inject_network_manager()
        except Exception as e:
            logger.error(f"Session integrity monitoring failed: {e}")

    def _handle_authentication_error(self, error: Exception) -> None:
        """Convert generic errors to specific proxy troubleshooting messages."""
        try:
            network_manager = NetworkManager()
            if not network_manager.is_proxy_enabled():
                raise error  # Not proxy-related, re-raise original error
            
            network_settings = network_manager.get_network_settings()
            proxy_url = "--"
            
            # Get proxy information from ProxyManager
            try:
                proxy_dict = network_manager._proxy_manager.get_current_proxy_dict()
                if proxy_dict:
                    # Use HTTPS proxy first, then HTTP proxy as fallback
                    if 'https' in proxy_dict:
                        proxy_url = proxy_dict['https']
                    elif 'http' in proxy_dict:
                        proxy_url = proxy_dict['http']
            except Exception as proxy_error:
                logger.warning(f"Failed to get proxy URL: {proxy_error}")
                # Try to get proxy settings directly
                if hasattr(network_manager, '_proxy_manager') and network_manager._proxy_manager._current_settings:
                    proxy_settings = network_manager._proxy_manager._current_settings
                    if proxy_settings.https_proxy:
                        proxy_url = proxy_settings.https_proxy
                    elif proxy_settings.http_proxy:
                        proxy_url = proxy_settings.http_proxy
            
            # Analyze error patterns
            error_msg = str(error).lower()
            
            if "407" in error_msg or "proxy authentication required" in error_msg:
                raise ProxyAuthenticationError(
                    proxy_url, "tidal_login", error
                ) from error
                
            elif "timeout" in error_msg:
                raise NetworkTimeoutError(
                    f"TIDAL authentication timed out through proxy {proxy_url}. "
                    f"Try: 1) Check proxy server status, 2) Increase timeout to {network_settings.api_timeout + 10}s, "
                    f"3) Verify proxy credentials"
                ) from error
                
            elif "connection" in error_msg or "unreachable" in error_msg:
                raise ProxyConnectionError(
                    f"Cannot connect to TIDAL through proxy {proxy_url}. "
                    f"Troubleshooting steps:\n"
                    f"1. Verify proxy server is running: {proxy_url}\n"
                    f"2. Check proxy credentials: username/password\n"  
                    f"3. Test proxy manually: curl --proxy {proxy_url} https://api.tidal.com\n"
                    f"4. Verify firewall allows proxy traffic"
                ) from error
            else:
                # Generic proxy-related error
                raise ProxyConnectionError(
                    f"TIDAL authentication failed through proxy {proxy_url}. "
                    f"Original error: {error}"
                ) from error
                
        except (ProxyConnectionError, NetworkTimeoutError, ProxyAuthenticationError):
            # Re-raise our custom exceptions
            raise
        except Exception:
            # If error handling itself fails, re-raise original error
            raise error

    def settings_apply(self, settings: Settings = None) -> bool:
        if settings:
            self.settings = settings

        self.session.audio_quality = self.settings.data.quality_audio
        self.session.video_quality = tidalapi.VideoQuality.high

        return True

    def login_token(self, do_pkce: bool = False) -> bool:
        result = False
        self.is_pkce = do_pkce

        if self.token_from_storage:
            try:
                # Monitor session integrity before authentication
                self._monitor_session_integrity()
                
                result = self.session.load_oauth_session(
                    self.data.token_type,
                    self.data.access_token,
                    self.data.refresh_token,
                    self.data.expiry_time,
                    is_pkce=do_pkce,
                )
            except (HTTPError, JSONDecodeError) as e:
                try:
                    # Handle authentication errors with proxy-specific messages
                    self._handle_authentication_error(e)
                except (ProxyConnectionError, NetworkTimeoutError, ProxyAuthenticationError) as proxy_error:
                    print(f"Authentication failed: {proxy_error}")
                    result = False
                except Exception:
                    # Fallback to original behavior for non-proxy errors
                    result = False
                    # Remove token file. Probably corrupt or invalid.
                    if os.path.exists(self.file_path):
                        os.remove(self.file_path)

                    print(
                        "Either there is something wrong with your credentials / account or some server problems on TIDALs "
                        "side. Anyway... Try to login again by re-starting this app."
                    )

        return result

    def login_finalize(self) -> bool:
        result = self.session.check_login()

        if result:
            self.token_persist()

        return result

    def token_persist(self) -> None:
        self.set_option("token_type", self.session.token_type)
        self.set_option("access_token", self.session.access_token)
        self.set_option("refresh_token", self.session.refresh_token)
        self.set_option("expiry_time", self.session.expiry_time)
        self.save()

    def login(self, fn_print: Callable) -> bool:
        is_token = self.login_token()
        result = False

        if is_token:
            fn_print("Yep, looks good! You are logged in.")
            result = True
        elif not is_token:
            fn_print("You either do not have a token or your token is invalid.")
            fn_print("No worries, we will handle this...")
            
            try:
                # Monitor session integrity before new authentication
                self._monitor_session_integrity()
                
                # Login method: Device linking
                self.session.login_oauth_simple(fn_print)
                # Login method: PKCE authorization (was necessary for HI_RES_LOSSLESS streaming earlier)
                # self.session.login_pkce(fn_print)

                is_login = self.login_finalize()

                if is_login:
                    fn_print("The login was successful. I have stored your credentials (token).")
                    result = True
                else:
                    fn_print("Something went wrong. Did you login using your browser correctly? May try again...")
                    
            except (ProxyConnectionError, NetworkTimeoutError, ProxyAuthenticationError) as proxy_error:
                fn_print(f"Authentication failed due to proxy issues: {proxy_error}")
                result = False
            except Exception as e:
                # Handle any other authentication errors
                try:
                    self._handle_authentication_error(e)
                except (ProxyConnectionError, NetworkTimeoutError, ProxyAuthenticationError) as proxy_error:
                    fn_print(f"Authentication failed: {proxy_error}")
                except Exception:
                    fn_print("Something went wrong. Did you login using your browser correctly? May try again...")
                result = False

        return result

    def logout(self):
        Path(self.file_path).unlink(missing_ok=True)
        self.token_from_storage = False
        del self.session

        return True


class HandlingApp(metaclass=SingletonMeta):
    event_abort: Event = Event()
    event_run: Event = Event()

    def __init__(self):
        self.event_run.set()
