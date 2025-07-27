class PackageData:
    def __init__(self,
                 type_=None,
                 repouuid=None,
                 checksum=None,
                 name=None,
                 arch=None,
                 ver_ver=None,
                 ver_epoch=None,
                 ver_rel=None,
                 summary=None,
                 description=None,
                 packager=None,
                 url=None,
                 time_file=None,
                 time_build=None,
                 size_pkg=None,
                 size_inst=None,
                 size_arc=None,
                 location_href=None,
                 checksum_type=None,
                 checksum_pkgid=None):

        self.type = type_
        self.repo_uuid = repouuid
        self.pkgid = checksum
        self.name = name
        self.arch = arch
        self.version = ver_ver
        self.epoch = ver_epoch
        self.release_ver = ver_rel
        self.summary = summary
        self.description = description
        self.packager = packager
        self.url = url
        self.time_file = time_file
        self.time_build = time_build
        self.size_package = size_pkg
        self.size_installed = size_inst
        self.size_archive = size_arc
        self.location = location_href
        self.checksum_type = checksum_type
        self.checksum_pkgid = checksum_pkgid
        self.checksum = checksum

        self.license = None
        self.vendor = None
        self.app_group = None
        self.buildhost = None
        self.sourcerpm = None
        self.header_start = None
        self.header_end = None

        self.requires = []
        self.provides = []
        self.conflicts = []
        self.obsoletes = []
        self.recommends = []
        self.suggests = []
        self.supplements = []
        self.enhances = []
        self.files = []

    def __repr__(self):
        return f"<PackageData name={self.name!r} version={self.version!r}-{self.release_ver!r}>"
