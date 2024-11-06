from shlex import quote

from bundlewrap.items.pkg import Pkg


class DnfPkg(Pkg):
    """
    A package installed by dnf.
    """
    BUNDLE_ATTRIBUTE_NAME = "pkg_dnf"
    ITEM_TYPE_NAME = "pkg_dnf"

    @classmethod
    def block_concurrent(cls, node_os, node_os_version):
        return ["pkg_dnf", "pkg_yum"]

    def pkg_all_installed(self):
        result = self.run("dnf list --installed")
        for line in result.stdout.decode('utf-8').strip().split("\n"):
            yield "{}:{}".format(self.ITEM_TYPE_NAME, line.split()[0].split(".")[0])

    def pkg_install(self):
        self.run("dnf -y install {}".format(quote(self.name)), may_fail=True)

    def pkg_installed(self):
        result = self.run(
            "dnf list --installed {}".format(quote(self.name)),
            may_fail=True,
        )
        return result.return_code == 0

    def pkg_remove(self):
        self.run("dnf -y remove {}".format(quote(self.name)), may_fail=True)
