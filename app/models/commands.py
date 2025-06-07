COMMAND_GUIDE = [
    {
        "id": "list_all_containers",
        "pattern": r"^(tampilkan|list|lihat)\s+semua\s+(?:container|kontainer)(s)?|docker\s+ps\s+-a$",
        "action": "list_containers",
        "params_map": {"all": True},
        "description": "Menampilkan semua kontainer (berjalan dan berhenti).",
        "example": "lihat semua containers / docker ps -a"
    },
    {
        "id": "list_running_containers",
        "pattern": r"^(?:tampilkan|list|lihat)\s+(?:(?:container|kontainer)(s)?(\s+(sedang\s+|yang\s+)?(jalan|aktif|running))?)?$|docker\s+ps$",
        "action": "list_containers",
        "params_map": {"all": False},
        "description": "Menampilkan hanya kontainer yang sedang berjalan.",
        "example": "list containers / docker ps"
    },
    {
        "id": "run_container",
        "pattern": r"^(jalankan|nyalakan|start|buat|run)\s+(?:(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)\s+(?:dari\s+image\s+)?(?P<image>[a-zA-Z0-9/:_.-]+)(?:\s+dengan\s+port(s)?\s+(?P<ports>\d{1,5}:\d{1,5}(?:,\d{1,5}:\d{1,5})*))?$",
        "action": "run_container",
        "description": "Menjalankan kontainer baru dari sebuah image. Opsional: 'dengan port HOST:CONTAINER'.",
        "example": "run webku nginx:latest dengan port 8080:80"
    },
    {
        "id": "start_container",
        "pattern": r"^(hidupkan|nyalakan|start|mulai)\s+(?:(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "start_container",
        "description": "Menghidupkan kembali kontainer yang sudah berhenti.",
        "example": "start webku"
    },
    {
        "id": "stop_container",
        "pattern": r"^(hentikan|matikan|stop)\s+(?:(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "stop_container",
        "description": "Menghentikan kontainer yang sedang berjalan.",
        "example": "stop webku"
    },
    {
        "id": "remove_container",
        "pattern": r"^(hapus|buang|remove|rm)\s+(?:(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "remove_container",
        "description": "Menghapus kontainer yang sudah berhenti.",
        "example": "rm webku_lama"
    },
    {
        "id": "view_logs",
        "pattern": r"^(?:(?:lihat|tampilkan)\s+log(s)?\s+(?:(?:dari\s+)?(?:kontainer|container|layanan|servis)\s+)?|docker\s+logs)\s+(?P<name>[a-zA-Z0-9_.-]+)(?:\s+sebanyak\s+(?P<lines>\d+)\s+baris)?$",
        "action": "view_logs",
        "description": "Menampilkan log dari sebuah kontainer. Opsional: 'sebanyak JUMLAH baris'.",
        "example": "docker logs webku sebanyak 50 baris"
    },
    {
        "id": "view_stats",
        "pattern": r"^(?:(?:lihat|tampilkan)\s+stats\s+(?:(?:dari\s+)?(?:kontainer|container)\s+)?|docker\s+stats)\s+(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "view_stats",
        "description": "Menampilkan statistik sumber daya dari sebuah kontainer.",
        "example": "docker stats webku"
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
        "pattern": r"^(tampilkan|list|lihat)\s+image(s)?|docker\s+images$",
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