from types import SimpleNamespace

import pytest

from iqpilot.common.params import Params
from iqpilot.selfdrive.ui.mici.layouts.settings import steering
from iqpilot.system.ui.widgets import DialogResult
from iqpilot.ui.layouts.settings import iq_panels


def test_set_convergence_defaults_on_and_remains_configurable(tmp_path):
  params = Params(str(tmp_path))
  assert params.get_default_value('expSpeedConv') is True
  params.put_bool('expSpeedConv', False)
  assert not params.get_bool('expSpeedConv')


@pytest.mark.parametrize('confirmed', [False, True])
def test_mici_no_nudge_waits_for_confirmation(monkeypatch, tmp_path, mocker, confirmed):
  params = Params(str(tmp_path))
  params.put('IQLaneChangeTimer', 0)
  selector = SimpleNamespace(_params=params, _param='IQLaneChangeTimer', refresh=mocker.Mock())
  selector._enable_no_nudge = lambda: steering.LaneChangeSelector._enable_no_nudge(selector)
  dialogs = []
  monkeypatch.setattr(steering.BigButton, '_handle_mouse_release', lambda *args: None)
  monkeypatch.setattr(steering, 'NoNudgeConfirmation', lambda callback: callback)
  monkeypatch.setattr(steering, 'gui_app', SimpleNamespace(push_widget=dialogs.append))

  steering.LaneChangeSelector._handle_mouse_release(selector, None)
  assert params.get('IQLaneChangeTimer') == 0
  assert len(dialogs) == 1
  if confirmed:
    dialogs[0]()
  assert params.get('IQLaneChangeTimer') == int(confirmed)


def test_mici_nudge_does_not_require_confirmation(monkeypatch, tmp_path, mocker):
  params = Params(str(tmp_path))
  params.put('IQLaneChangeTimer', 1)
  selector = SimpleNamespace(_params=params, _param='IQLaneChangeTimer', refresh=mocker.Mock())
  monkeypatch.setattr(steering.BigButton, '_handle_mouse_release', lambda *args: None)
  push = mocker.Mock()
  monkeypatch.setattr(steering, 'gui_app', SimpleNamespace(push_widget=push))
  steering.LaneChangeSelector._handle_mouse_release(selector, None)
  assert params.get('IQLaneChangeTimer') == 0
  push.assert_not_called()


@pytest.mark.parametrize('result', [DialogResult.CANCEL, DialogResult.CONFIRM])
def test_big_no_nudge_waits_for_confirmation(monkeypatch, tmp_path, mocker, result):
  params = Params(str(tmp_path))
  params.put('IQLaneChangeTimer', 0)
  action = mocker.Mock()
  panel = SimpleNamespace(_lane_change_setting=SimpleNamespace(action_item=action))
  dialogs = []
  monkeypatch.setattr(iq_panels, 'ui_state', SimpleNamespace(params=params))
  monkeypatch.setattr(iq_panels, 'ConfirmDialog', lambda *args: args)
  monkeypatch.setattr(iq_panels, 'gui_app', SimpleNamespace(set_modal_overlay=lambda dialog, callback: dialogs.append(callback)))

  iq_panels.SteeringLayout._set_lane_change_mode(panel, 1)
  assert params.get('IQLaneChangeTimer') == 0
  action.set_selected_button.assert_called_once_with(0)
  dialogs[0](result)
  assert params.get('IQLaneChangeTimer') == int(result == DialogResult.CONFIRM)


def test_big_nudge_does_not_require_confirmation(monkeypatch, tmp_path, mocker):
  params = Params(str(tmp_path))
  params.put('IQLaneChangeTimer', 1)
  monkeypatch.setattr(iq_panels, 'ui_state', SimpleNamespace(params=params))
  overlay = mocker.Mock()
  monkeypatch.setattr(iq_panels, 'gui_app', SimpleNamespace(set_modal_overlay=overlay))
  iq_panels.SteeringLayout._set_lane_change_mode(SimpleNamespace(), 0)
  assert params.get('IQLaneChangeTimer') == 0
  overlay.assert_not_called()
