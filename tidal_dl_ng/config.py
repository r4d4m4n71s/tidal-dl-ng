import json
import os
import shutil
from collections.abc import Callable
from json import JSONDecodeError
from pathlib import Path
from threading import Event
from typing import Any, Optional

import tidalapi
from requests import HTTPError

from tidal_dl_ng.helper.decorator import SingletonMeta
from tidal_dl_ng.helper.path import path_config_base, path_file_settings, path_file_token
from tidal_dl_ng.model.cfg import Settings as ModelSettings
from tidal_dl_ng.model.cfg import Token as ModelToken
from tidal_dl_ng.model.cfg import ProxyConfig, ProxySettings
from tidal_dl_ng.proxy import ProxyManager
from tidal_dl_ng.auth_server import LocalAuthServer
from tidal_dl_ng.enhanced_session import EnhancedTidalSession, create_enhanced_tidal_session
from tidal_dl_ng.tidal_proxy_integration import TidalProxyIntegration


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


class Tidal(BaseConfig, metaclass=SingletonMeta):
    session: EnhancedTidalSession
    token_from_storage: bool = False
    settings: Settings
    is_pkce: bool
    proxy_manager: Optional[ProxyManager] = None
    auth_server: Optional[LocalAuthServer] = None
    tidal_integration: Optional[TidalProxyIntegration] = None

    def __init__(self, settings: Settings = None):
        self.cls_model = ModelToken
        self.file_path = path_file_token()
        self.token_from_storage = self.read(self.file_path)

        if settings:
            self.settings = settings
            # Create proxy-enhanced session using the integration layer
            self.session = create_enhanced_tidal_session(
                settings=settings,
                quality=settings.data.quality_audio,
                video_quality=tidalapi.VideoQuality.high
            )
            self.tidal_integration = TidalProxyIntegration(settings)
            self.settings_apply()
            self._init_proxy_manager()
        else:
            # Fallback to standard session if no settings provided
            tidal_config: tidalapi.Config = tidalapi.Config(item_limit=10000)
            self.session = EnhancedTidalSession(tidal_config)

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
                result = self.session.load_oauth_session(
                    self.data.token_type,
                    self.data.access_token,
                    self.data.refresh_token,
                    self.data.expiry_time,
                    is_pkce=do_pkce,
                )
            except (HTTPError, JSONDecodeError):
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
        """Enhanced login method with comprehensive proxy and local server support."""
        is_token = self.login_token()
        result = False

        if is_token:
            fn_print("Yep, looks good! You are logged in.")
            result = True
        elif not is_token:
            fn_print("You either do not have a token or your token is invalid.")
            fn_print("No worries, we will handle this...")
            
            # Priority 1: Use local server authentication if available and enabled
            if (self.auth_server and 
                self.settings.data.auth_settings.use_local_server and 
                self.proxy_manager and 
                self.proxy_manager.settings.enabled):
                
                fn_print("Using local server authentication with proxy...")
                success, error = self.auth_server.authenticate_with_tidal(self.session)
                
                if success:
                    result = self.login_finalize()
                    if result:
                        fn_print("The login was successful. I have stored your credentials (token).")
                    else:
                        fn_print("Token validation failed after authentication.")
                else:
                    fn_print(f"Local server authentication failed: {error}")
                    # Fallback to proxy-enhanced device linking
                    fn_print("Falling back to proxy-enhanced device linking...")
                    result = self._perform_device_linking(fn_print)
            
            # Priority 2: Use proxy-enhanced device linking if proxy is available
            elif self.session.proxy_manager:
                fn_print("Using proxy-enhanced authentication...")
                result = self._perform_device_linking(fn_print)
            
            # Priority 3: Use standard device linking as fallback
            else:
                fn_print("Using standard authentication...")
                result = self._perform_device_linking(fn_print)

        return result

    def _perform_device_linking(self, fn_print: Callable) -> bool:
        """Perform device linking authentication with proxy support if available."""
        # Use proxy-aware login if proxy manager is available
        if self.session.proxy_manager:
            self.session.login_oauth_simple_with_proxy(fn_print)
        else:
            # Traditional device linking method
            self.session.login_oauth_simple(fn_print)
        
        # Alternative: PKCE authorization (was necessary for HI_RES_LOSSLESS streaming earlier)
        # if self.session.proxy_manager:
        #     self.session.login_pkce_with_proxy(fn_print)
        # else:
        #     self.session.login_pkce(fn_print)

        is_login = self.login_finalize()

        if is_login:
            fn_print("The login was successful. I have stored your credentials (token).")
            return True
        else:
            fn_print("Something went wrong. Did you login using your browser correctly? May try again...")
            return False

    def _init_proxy_manager(self):
        """Initialize proxy manager from settings."""
        if self.settings and self.settings.data.proxy_settings.enabled:
            # Use the proxy settings directly since they're already compatible
            self.proxy_manager = ProxyManager(self.settings.data.proxy_settings)
            
            # Initialize auth server if local server auth is enabled
            if self.settings.data.auth_settings.use_local_server:
                self.auth_server = LocalAuthServer(self.proxy_manager, self.settings.data.auth_settings)
            
            print(f"Proxy manager initialized with {len(self.settings.data.proxy_settings.proxies)} proxy(ies)")
        else:
            print("Proxy not enabled or no proxies configured")


    
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
