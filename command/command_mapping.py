__all__ = ["SessionCommandMapping", \
           "WindowCommandMapping", \
           "ElementCommandMapping"]

from base.bind import Bind
from window_commands import *
from session_commands import *
from alert_commands import *
from element_commands import *
from init_session_commands import ExecuteGetStatus

# session commands map
SessionCommandMapping = {r'/status$': {'GET': Bind(ExecuteGetStatus)},
                         r'/session/([a-f0-9]+)$': {'GET': Bind(ExecuteGetSessionCapabilities)},
                         r'/session/([a-f0-9]+)/timeouts/implicit_wait$': {'POST': Bind(ExecuteImplicitlyWait)},
                         r'/session/([a-f0-9]+)/timeouts$': {'POST': Bind(ExecuteSetTimeout)},
                         r'/session/([a-f0-9]+)/timeouts/async_script$': {'POST': Bind(ExecuteSetScriptTimeout)},
                         r'/session/([a-f0-9]+)/window_handle$': {'GET': Bind(ExecuteGetCurrentWindowHandle)},
                         r'/session/([a-f0-9]+)/window_handles$': {'GET': Bind(ExecuteGetWindowHandles)},
                         r'/session/([a-f0-9]+)/is_loading$': {'GET': Bind(ExecuteIsLoading)},
                         r'/session/([a-f0-9]+)/orientation$': {'GET': Bind(ExecuteGetBrowserOrientation)},
                         r'/session/([a-f0-9]+)/location$': {'GET': Bind(ExecuteGetLocation)},
                         r'/session/([a-f0-9]+)/application_cache/status$': {'GET': Bind(ExecuteGetAppCacheStatus)},
                         r'/session/([a-f0-9]+)/window$': {'DELETE': Bind(ExecuteClose),
                                                           'POST': Bind(ExecuteSwitchToWindow)}}

# window commands map
WindowCommandMapping = {r'/session/([a-f0-9]+)/title$': {'GET': Bind(ExecuteGetTitle)},
                        r'/session/([a-f0-9]+)/refresh$': {'POST': Bind(ExecuteRefresh)},
                        r'/session/([a-f0-9]+)/url$': {'GET': Bind(ExecuteGetCurrentUrl),
                                                       'POST': Bind(ExecuteGet)},
                        r'/session/([a-f0-9]+)/source$': {'GET': Bind(ExecuteGetPageSource)},
                        r'/session/([a-f0-9]+)/browser_connection$': {'GET': Bind(ExecuteIsBrowserOnline)},
                        r'/session/([a-f0-9]+)/back$': {'POST': Bind(ExecuteGoBack)},
                        r'/session/([a-f0-9]+)/forward$': {'POST': Bind(ExecuteGoForward)},
                        r'/session/([a-f0-9]+)/element$': {'POST': Bind(ExecuteFindElement)},
                        r'/session/([a-f0-9]+)/elements$': {'POST': Bind(ExecuteFindElements)},
                        r'/session/([a-f0-9]+)/execute$': {'POST': Bind(ExecuteExecuteScript)},
                        r'/session/([a-f0-9]+)/execute_async$': {'POST': Bind(ExecuteExecuteAsyncScript)},
                        r'/session/([a-f0-9]+)/screenshot$': {'GET': Bind(ExecuteScreenshot)},
                        r'/session/([a-f0-9]+)/window/([\-\w]+)/size$': {'GET': Bind(ExecuteGetWindowSize)},
                        r'/session/([a-f0-9]+)/window/([\-\w]+)/position$': {'GET': Bind(ExecuteGetWindowPosition)},
                        r'/session/([a-f0-9]+)/cookie$': {'GET': Bind(ExecuteGetCookies),
                                                          'POST': Bind(ExecuteAddCookie),
                                                          'DELETE': Bind(ExecuteDeleteAllCookies)},
                        r'/session/([a-f0-9]+)/cookie/([\S]+)$': {'DELETE': Bind(ExecuteDeleteCookie)},
                        r'/session/([a-f0-9]+)/frame$': {'POST': Bind(ExecuteSwitchToFrame)}}

# alert commands map
AlertCommandMapping = {r'/session/([a-f0-9]+)/accept_alert$': {'POST': Bind(ExecuteAcceptAlert)}}

# element commands map
ElementCommandMapping = {r'/session/([a-f0-9]+)/element/([.\-0-9]+)/text$': {'GET': Bind(ExecuteGetElementText)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/name$': {'GET': Bind(ExecuteGetElementTagName)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/selected$': {'GET': Bind(ExecuteIsElementSelected)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/enabled$': {'GET': Bind(ExecuteIsElementEnabled)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/displayed$': {'GET': Bind(ExecuteIsElementDisplayed)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/size$': {'GET': Bind(ExecuteGetElementSize)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/location$': {'GET': Bind(ExecuteGetElementLocation)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/clear$': {'POST': Bind(ExecuteClearElement)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/attribute/(\w+)$': {'GET': Bind(ExecuteGetElementAttribute)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/value$': {'GET': Bind(ExecuteGetElementValue),
                                                                              'POST': Bind(ExecuteSendKeysToElement)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/css/(.+)$': {'GET': Bind(ExecuteGetElementValueOfCSSProperty)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/equals/(.+)$': {'GET': Bind(ExecuteElementEquals)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/submit$': {'POST': Bind(ExecuteSubmitElement)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/location_in_view$': {'GET': Bind(ExecuteGetElementLocationOnceScrolledIntoView)},
                         r'/session/([a-f0-9]+)/element/([.\-0-9]+)/click$': {'POST': Bind(ExecuteClickElement)}}

