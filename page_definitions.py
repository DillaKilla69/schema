from schema import Row, Page

PAGES: tuple[Page, ...] = (
    Page(
        name="Network",
        rows=(
            Row(name="Firewall", options=("allow", "deny", "log")),
            Row(name="VPN", options=("split-tunnel", "full-tunnel", "disabled")),
            Row(name="DNS", options=("internal", "external", "both")),
            Row(name="Proxy", options=("http", "https", "socks5")),
        ),
    ),
    Page(
        name="Storage",
        rows=(
            Row(name="Primary Disk", options=("ssd", "hdd", "nvme")),
            Row(name="Backup", options=("daily", "weekly", "monthly", "off")),
            Row(name="Archive", options=("cold", "warm", "hot")),
            Row(name="Encryption", options=("aes-128", "aes-256", "none")),
            Row(name="Compression", options=("lz4", "zstd", "gzip", "none")),
        ),
    ),
    Page(
        name="Compute",
        rows=(
            Row(name="CPU Profile", options=("low-power", "balanced", "performance")),
            Row(name="Memory Mode", options=("normal", "huge-pages", "swap-disabled")),
            Row(name="GPU", options=("integrated", "discrete", "offload")),
        ),
    )
)
