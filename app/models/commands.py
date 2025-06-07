COMMAND_GUIDE = [
    {
        "id": "list_all_containers",
        "pattern": r"^(?:tampilkan|list|lihat)\s+semua\s+(?:container|kontainer)(s)?|docker\s+ps\s+-a$",
        "action": "list_containers",
        "params_map": {"all": True},
        "description": "Menampilkan semua kontainer (berjalan dan berhenti).",
        "example": "lihat semua containers / docker ps -a"
    },
    {
        "id": "list_running_containers",
        "pattern": r"^(?:tampilkan|list|lihat)\s+(?:(?:container|kontainer)(s)?(?:(?:\s+sedang|\s+yang)?\s+(?:jalan|aktif|running))?)?$|docker\s+ps$",
        "action": "list_containers",
        "params_map": {"all": False},
        "description": "Menampilkan hanya kontainer yang sedang berjalan.",
        "example": "list containers / docker ps"
    },
    {
        "id": "run_container_from_name",
        "pattern": r"^(?:jalankan|nyalakan|start|buat|run)\s+(?:(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)\s+(?:dari\s+image\s+)?(?P<image>[a-zA-Z0-9/:_.-]+)(?:\s+dengan\s+port(?:s)?\s+(?P<ports>\d{1,5}:\d{1,5}(?:,\d{1,5}:\d{1,5})*))?$",
        "action": "run_container",
        "description": "Menjalankan kontainer baru (Format: run NAMA dari IMAGE).",
        "example": "run webku nginx:latest dengan port 8080:80"
    },
    {
        "id": "run_container_from_image",
        "pattern": r"^(?:jalankan|nyalakan|start|buat|run)\s+(?:dari\s+)?image\s+(?P<image>[a-zA-Z0-9/:_.-]+)\s+(?:sebagai|as)\s+(?:(?:kontainer|container)\s+)?(?P<name>[a-zA-Z0-9_.-]+)(?:\s+dengan\s+port(?:s)?\s+(?P<ports>\d{1,5}:\d{1,5}(?:,\d{1,5}:\d{1,5})*))?$",
        "action": "run_container",
        "description": "Menjalankan kontainer baru (Format: run image IMAGE as NAMA).",
        "example": "run image nginx:latest as webku"
    },
    {
        "id": "start_container",
        "pattern": r"^(?:(?:hidupkan|nyalakan|start|mulai)\s+(?:(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)|(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+(?:hidupkan|nyalakan|start|mulai))$",
        "action": "start_container",
        "description": "Menghidupkan kembali kontainer yang sudah berhenti.",
        "example": "start webku / container webku start"
    },
    {
        "id": "stop_container",
        "pattern": r"^(?:(?:hentikan|matikan|stop)\s+(?:(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)|(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+(?:hentikan|matikan|stop))$",
        "action": "stop_container",
        "description": "Menghentikan kontainer yang sedang berjalan.",
        "example": "stop webku / container webku stop"
    },
    {
        "id": "remove_container",
        "pattern": r"^(?:(?:hapus|buang|remove|rm)\s+(?:(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)|(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+(?:hapus|buang|remove|rm))$",
        "action": "remove_container",
        "description": "Menghapus kontainer yang sudah berhenti.",
        "example": "rm webku_lama / container webku_lama rm"
    },
    {
        "id": "view_logs",
        "pattern": r"^(?:(?:(?:lihat|tampilkan)\s+log(?:s)?|docker\s+logs)\s+(?:(?:dari\s+)?(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)|(?:lihat|tampilkan)\s+(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+log(?:s)?)(?:\s+sebanyak\s+(?P<lines>\d+)\s+baris)?$",
        "action": "view_logs",
        "description": "Menampilkan log dari sebuah kontainer. Opsional: 'sebanyak JUMLAH baris'.",
        "example": "lihat log container webku / lihat container webku log"
    },
    {
        "id": "view_stats",
        "pattern": r"^(?:(?:(?:lihat|tampilkan)\s+stats|docker\s+stats)\s+(?:(?:dari\s+)?(?:kontainer|container)\s+)?(?P<name>[a-zA-Z0-9_.-]+)|(?:lihat|tampilkan)\s+(?:kontainer|container)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+stats)$",
        "action": "view_stats",
        "description": "Menampilkan statistik sumber daya dari sebuah kontainer.",
        "example": "lihat stats container webku / lihat container webku stats"
    },
    {
        "id": "pull_image",
        "pattern": r"^(?:(?:tarik|pull)\s+image|docker\s+pull)\s+(?P<image>[a-zA-Z0-9/:_.-]+)$",
        "action": "pull_image",
        "description": "Menarik (pull) image dari registry.",
        "example": "docker pull alpine:latest"
    },
    {
        "id": "list_images",
        "pattern": r"^(?:tampilkan|list|lihat)\s+image(?:s)?|docker\s+images$",
        "action": "list_images",
        "description": "Menampilkan semua image Docker yang ada di lokal.",
        "example": "docker images"
    },
    {
        "id": "compose_up",
        "pattern": r"^compose-?up(?:\s+(?P<service>[a-zA-Z0-9_.-]+))?$",
        "action": "compose_up",
        "description": "Menjalankan 'docker-compose up -d'. Menerima 'compose up' dan 'compose-up'.",
        "example": "compose-up my_service"
    },
    {
        "id": "compose_down",
        "pattern": r"^compose-?down$",
        "action": "compose_down",
        "description": "Menjalankan 'docker-compose down'. Menerima 'compose down' dan 'compose-down'.",
        "example": "compose-down"
    }
]