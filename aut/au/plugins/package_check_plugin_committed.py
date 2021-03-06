# =============================================================================
# package_check_plugin_committed.py  - Plugin to capture
# committed packages on the system.
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
from au.plugins.plugin import IPlugin


class CommittedPackagesPlugin(IPlugin):

    """
    ASR9k Pre-upgrade check
    This plugin checks the packages state
    """
    NAME = "COMMITTED_PACKAGES"
    DESCRIPTION = "Committed Package Check"
    TYPE = "PRE_UPGRADE"
    VERSION = "0.1.1"

    def save_packages(self, data, outfile):
        with open(outfile, "w") as f:
            f.write(data)
        return

    def start(self, device, *args, **kwargs):
        if device:
            success, output = device.execute_command(
                "admin show install commit summary")
            if success:
                self.csm_ctx = device.get_property('ctx')
                if self.csm_ctx and hasattr(self.csm_ctx, 'committed_cli'):
                    self.csm_ctx.committed_cli = output
                self.log("Committed packages retrieved")
                device.store_property('install_commit', output)
                return

        self.error("Can not get list of committed packages.")
