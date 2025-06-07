COMMAND_GUIDE = [
    {
        "id": "list_all_containers",
        "pattern": r"^(tampilkan|list|lihat)\s+(semua\s+)?container(s)?$",
        "action": "list_containers",
        "params_map": {"all": True},
        "description": "Menampilkan semua kontainer (berjalan dan berhenti).",
        "example": "list containers"
    },
    {
        "id": "list_running_containers",
        "pattern": r"^(tampilkan|list|lihat)\s+container(s)?\s+(sedang\s+|yang\s+)?(jalan|aktif|running)$",
        "action": "list_containers",
        "params_map": {"all": False},
        "description": "Menampilkan hanya kontainer yang sedang berjalan.",
        "example": "list container yang jalan"
    },
    {
        "id": "run_container",
        "pattern": r"^(jalankan|nyalakan|start)\s+(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+dari\s+image\s+(?P<image>[a-zA-Z0-9/:_.-]+)(?:\s+dengan\s+port\s+(?P<ports>\d{1,5}:\d{1,5}(?:,\d{1,5}:\d{1,5})*))?$",
        "action": "run_container",
        "description": "Menjalankan kontainer baru dari sebuah image. Opsional: 'dengan port HOST:CONTAINER,HOST2:CONTAINER2'.",
        "example": "jalankan webku dari image nginx:latest dengan port 8080:80"
    },
    {
        "id": "stop_container",
        "pattern": r"^(hentikan|matikan|stop)\s+(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "stop_container",
        "description": "Menghentikan kontainer yang sedang berjalan berdasarkan namanya.",
        "example": "stop webku"
    },
    {
        "id": "remove_container",
        "pattern": r"^(hapus|buang|remove)\s+(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "remove_container",
        "description": "Menghapus kontainer yang sudah berhenti berdasarkan namanya.",
        "example": "hapus webku"
    },
    {
        "id": "view_logs",
        "pattern": r"^(lihat|tampilkan)\s+log(s)?\s+(?:dari\s+)?(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)(?:\s+sebanyak\s+(?P<lines>\d+)\s+baris)?$",
        "action": "view_logs",
        "description": "Menampilkan log dari sebuah kontainer. Opsional: 'sebanyak JUMLAH baris'.",
        "example": "lihat log webku sebanyak 50 baris"
    },
    {
        "id": "view_stats",
        "pattern": r"^(lihat|tampilkan)\s+stats\s+(?:dari\s+)?(?:kontainer|container)\s+(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "view_stats",
        "description": "Menampilkan statistik penggunaan sumber daya (CPU & Memori) dari sebuah kontainer.",
        "example": "lihat stats webku"
    },
    {
        "id": "pull_image",
        "pattern": r"^(tarik|pull)\s+image\s+(?P<image>[a-zA-Z0-9/:_.-]+)$",
        "action": "pull_image",
        "description": "Menarik (pull) image dari registry.",
        "example": "pull image alpine:latest"
    },
    {
        "id": "list_images",
        "pattern": r"^(tampilkan|list|lihat)\s+image(s)?$",
        "action": "list_images",
        "description": "Menampilkan semua image Docker yang ada di lokal.",
        "example": "list images"
    },
    {
        "id": "compose_up",
        "pattern": r"^compose\s+up(?:\s+(?P<service>[a-zA-Z0-9_.-]+))?$",
        "action": "compose_up",
        "description": "Menjalankan 'docker-compose up -d' untuk semua layanan atau layanan spesifik (flag -d ditambahkan otomatis).",
        "example": "compose up my_service"
    },
    {
        "id": "compose_down",
        "pattern": r"^compose\s+down$",
        "action": "compose_down",
        "description": "Menjalankan 'docker-compose down'.",
        "example": "compose down"
    }
]