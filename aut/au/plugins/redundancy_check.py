# =============================================================================
# redundancy_check.py -- plugin to parse and check show redundancy
#
# Copyright (c)  2013, Cisco Systems
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
# =============================================================================


from au.lib.global_constants import *

from au.plugins import IPlugin


class NodeRedundancyPlugin(IPlugin):

    """
    ASR9k Pre-upgrade check
    This plugin checks Standby state
    """
    NAME = "NODE_REDUNDANCY"
    DESCRIPTION = "Node Redundancy Check"
    TYPE = "PRE_UPGRADE"
    VERSION = "0.1.1"

    def start(self, device, *args, **kwargs):
        """
        """
        if not device:
            self.error("Device error")

        success, output = device.execute_command(
            "admin show redundancy location all"
        )
        if not success:
            self.error("Show redundancy output failed.")

        lines = output.split("\n", 50)

        if len(lines) < 6:
            self.error("Show redundancy output is insufficient.")

        for ln, line in enumerate(lines[:6]):
            if "is in STANDBY role" in line:
                if "is ready" in lines[ln + 1]:
                    return
                else:
                    self.error(
                        "Standby is not ready. Upgrade can not proceed.")
