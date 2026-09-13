# Copyright 2025 Apheleia
#
# Description:
# Apheleia Verification Library IEEE 1149.1 TAP state machine

from enum import Enum


class TapState(Enum):
    """
    IEEE 1149.1 TAP controller states.

    Names match those used by OpenOCD (``pathmove``, ``-endstate``).
    """

    RESET = "RESET"
    IDLE = "IDLE"
    DRSELECT = "DRSELECT"
    DRCAPTURE = "DRCAPTURE"
    DRSHIFT = "DRSHIFT"
    DREXIT1 = "DREXIT1"
    DRPAUSE = "DRPAUSE"
    DREXIT2 = "DREXIT2"
    DRUPDATE = "DRUPDATE"
    IRSELECT = "IRSELECT"
    IRCAPTURE = "IRCAPTURE"
    IRSHIFT = "IRSHIFT"
    IREXIT1 = "IREXIT1"
    IRPAUSE = "IRPAUSE"
    IREXIT2 = "IREXIT2"
    IRUPDATE = "IRUPDATE"

    def next(self, tms: int) -> "TapState":
        """
        Return the state entered on a TCK rising edge with the given TMS value.

        :param tms: Value of TMS sampled on the rising edge of TCK
        :type tms: int
        :return: The next TAP state
        :rtype: TapState
        """
        return _TRANSITIONS[self][1 if tms else 0]


S = TapState
_TRANSITIONS = {
    #                (TMS=0,       TMS=1)
    S.RESET:     (S.IDLE,      S.RESET),
    S.IDLE:      (S.IDLE,      S.DRSELECT),
    S.DRSELECT:  (S.DRCAPTURE, S.IRSELECT),
    S.DRCAPTURE: (S.DRSHIFT,   S.DREXIT1),
    S.DRSHIFT:   (S.DRSHIFT,   S.DREXIT1),
    S.DREXIT1:   (S.DRPAUSE,   S.DRUPDATE),
    S.DRPAUSE:   (S.DRPAUSE,   S.DREXIT2),
    S.DREXIT2:   (S.DRSHIFT,   S.DRUPDATE),
    S.DRUPDATE:  (S.IDLE,      S.DRSELECT),
    S.IRSELECT:  (S.IRCAPTURE, S.RESET),
    S.IRCAPTURE: (S.IRSHIFT,   S.IREXIT1),
    S.IRSHIFT:   (S.IRSHIFT,   S.IREXIT1),
    S.IREXIT1:   (S.IRPAUSE,   S.IRUPDATE),
    S.IRPAUSE:   (S.IRPAUSE,   S.IREXIT2),
    S.IREXIT2:   (S.IRSHIFT,   S.IRUPDATE),
    S.IRUPDATE:  (S.IDLE,      S.DRSELECT),
}
del S

__all__ = ["TapState"]
