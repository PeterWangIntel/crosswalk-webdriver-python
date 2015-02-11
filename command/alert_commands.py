__all__ = ["ExecuteAlertCommand", \
           "ExecuteAcceptAlert"]

from browser.web_view_impl import WebViewImpl
from browser.status import *
from base.log import VLOG

def ExecuteAlertCommand(alert_command, session, params, value):
  web_view = WebViewImpl("fake_id", 0, None)
  # update web_view
  status = session.GetTargetWindow(web_view)
  if status.IsError():
    return status

  status = web_view.ConnectIfNecessary()
  if status.IsError():
    return status

  status = web_view.HandleReceivedEvents()
  if status.IsError():
    return status

  status = web_view.WaitForPendingNavigations(session.GetCurrentFrameId(), session.page_load_timeout, True)
  if status.IsError() and status.Code() != kUnexpectedAlertOpen:
    return status

  alert_command.Update([session, web_view, params, value])
  return alert_command.Run(session, web_view, params, value)

def ExecuteAcceptAlert(session, web_view, params, value):
  status = web_view.GetJavaScriptDialogManager().HandleDialog(True, session.prompt_text)
  session.prompt_text = ""
  return status

