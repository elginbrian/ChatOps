COMMAND_GUIDE = [
    {
        "id": "list_all_containers",
        "pattern": r"^(?:tampilkan|list|lihat)\s+semua\s+(?:container|kontainer)(?:s)?|docker\s+ps\s+-a$",
        "action": "list_containers",
        "params_map": {"all": True},
        "description": "Menampilkan semua kontainer (berjalan dan berhenti).",
        "example": "lihat semua containers"
    },
    {
        "id": "list_running_containers",
        "pattern": r"^(?:tampilkan|list|lihat)\s+(?:(?:container|kontainer)(?:s)?(?:(?:\s+sedang|\s+yang)?\s+(?:jalan|aktif|running))?)?$|docker\s+ps$",
        "action": "list_containers",
        "params_map": {"all": False},
        "description": "Menampilkan hanya kontainer yang sedang berjalan.",
        "example": "list containers"
    },
    {
        "id": "run_container_name_first",
        "pattern": r"^(?:jalankan|nyalakan|start|buat|run)\s+(?:(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)\s+(?:dari\s+image\s+)?(?P<image>[a-zA-Z0-9/:_.-]+)(?:\s+dengan\s+port(?:s)?\s+(?P<ports>\d{1,5}:\d{1,5}(?:,\d{1,5}:\d{1,5})*))?$",
        "action": "run_container",
        "description": "Menjalankan kontainer baru (Format: run NAMA dari IMAGE).",
        "example": "run webku nginx:latest"
    },
    {
        "id": "run_container_image_first",
        "pattern": r"^(?:jalankan|nyalakan|start|buat|run)\s+(?:dari\s+)?image\s+(?P<image>[a-zA-Z0-9/:_.-]+)\s+(?:sebagai|as)\s+(?:(?:kontainer|container)\s+)?(?P<name>[a-zA-Z0-9_.-]+)(?:\s+dengan\s+port(?:s)?\s+(?P<ports>\d{1,5}:\d{1,5}(?:,\d{1,5}:\d{1,5})*))?$",
        "action": "run_container",
        "description": "Menjalankan kontainer baru (Format: run image IMAGE as NAMA).",
        "example": "run image nginx:latest as webku"
    },
    {
        "id": "start_container_verb_first",
        "pattern": r"^(?:hidupkan|nyalakan|start|mulai)\s+(?:(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "start_container",
        "description": "Menghidupkan kontainer (Format: start NAMA).",
        "example": "start webku"
    },
    {
        "id": "start_container_noun_first",
        "pattern": r"^(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+(?:hidupkan|nyalakan|start|mulai)$",
        "action": "start_container",
        "description": "Menghidupkan kontainer (Format: container NAMA start).",
        "example": "container webku start"
    },
    {
        "id": "stop_container_verb_first",
        "pattern": r"^(?:hentikan|matikan|stop)\s+(?:(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "stop_container",
        "description": "Menghentikan kontainer (Format: stop NAMA).",
        "example": "stop webku"
    },
    {
        "id": "stop_container_noun_first",
        "pattern": r"^(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+(?:hentikan|matikan|stop)$",
        "action": "stop_container",
        "description": "Menghentikan kontainer (Format: container NAMA stop).",
        "example": "container webku stop"
    },
    {
        "id": "remove_container_verb_first",
        "pattern": r"^(?:hapus|buang|remove|rm)\s+(?:(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "remove_container",
        "description": "Menghapus kontainer (Format: rm NAMA).",
        "example": "rm webku_lama"
    },
    {
        "id": "remove_container_noun_first",
        "pattern": r"^(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+(?:hapus|buang|remove|rm)$",
        "action": "remove_container",
        "description": "Menghapus kontainer (Format: container NAMA rm).",
        "example": "container webku_lama rm"
    },
    {
        "id": "view_logs_verb_first",
        "pattern": r"^(?:(?:lihat|tampilkan)\s+log(?:s)?|docker\s+logs)\s+(?:(?:dari\s+)?(?:kontainer|container|layanan|servis)\s+)?(?P<name>[a-zA-Z0-9_.-]+)(?:\s+sebanyak\s+(?P<lines>\d+)\s+baris)?$",
        "action": "view_logs",
        "description": "Melihat log kontainer (Format: lihat log NAMA).",
        "example": "lihat log webku"
    },
    {
        "id": "view_logs_noun_first",
        "pattern": r"^(?:lihat|tampilkan)\s+(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+log(?:s)?(?:\s+sebanyak\s+(?P<lines>\d+)\s+baris)?$",
        "action": "view_logs",
        "description": "Melihat log kontainer (Format: lihat container NAMA log).",
        "example": "lihat container webku log"
    },
    {
        "id": "view_stats_verb_first",
        "pattern": r"^(?:(?:lihat|tampilkan)\s+stats|docker\s+stats)\s+(?:(?:dari\s+)?(?:kontainer|container)\s+)?(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "view_stats",
        "description": "Melihat statistik kontainer (Format: lihat stats NAMA).",
        "example": "lihat stats webku"
    },
    {
        "id": "view_stats_noun_first",
        "pattern": r"^(?:lihat|tampilkan)\s+(?:kontainer|container)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+stats$",
        "action": "view_stats",
        "description": "Melihat statistik kontainer (Format: lihat container NAMA stats).",
        "example": "lihat container webku stats"
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
        "description": "Menjalankan 'docker-compose up -d'.",
        "example": "compose-up my_service"
    },
    {
        "id": "compose_down",
        "pattern": r"^compose-?down$",
        "action": "compose_down",
        "description": "Menjalankan 'docker-compose down'.",
        "example": "compose-down"
    },
    {
        "id": "list_volumes",
        "pattern": r"^(?:tampilkan|list|lihat)\s+volume(?:s)?|docker\s+volume\s+ls$",
        "action": "list_volumes",
        "description": "Menampilkan semua volume Docker.",
        "example": "list volumes"
    },
    {
        "id": "remove_volume",
        "pattern": r"^(?:hapus|rm)\s+volume\s+(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "remove_volume",
        "description": "Menghapus volume yang tidak terpakai.",
        "example": "rm volume data_lama"
    },
    {
        "id": "list_networks",
        "pattern": r"^(?:tampilkan|list|lihat)\s+network(?:s)?|docker\s+network\s+ls$",
        "action": "list_networks",
        "description": "Menampilkan semua network Docker.",
        "example": "list networks"
    },
    {
        "id": "inspect_object",
        "pattern": r"^(?:periksa|inspect|detail)\s+(?P<object_type>container|kontainer|image|volume|network)\s+(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "inspect_object",
        "description": "Menampilkan informasi detail (JSON) dari sebuah objek.",
        "example": "inspect container webku"
    },
    {
        "id": "system_prune",
        "pattern": r"^(?:sistem\s+bersihkan|system\s+prune)$",
        "action": "prune_system",
        "description": "Membersihkan kontainer, image, volume, dan network yang tidak terpakai.",
        "example": "system prune"
    },
    {
        "id": "restart_container",
        "pattern": r"^(?:restart|mulai ulang)\s+(?:(?:kontainer|container)\s+)?(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "restart_container",
        "description": "Me-restart kontainer yang sedang berjalan.",
        "example": "restart webku"
    },
    {
        "id": "remove_image",
        "pattern": r"^(?:hapus|rm|remove)\s+image\s+(?P<name>[a-zA-Z0-9/:_.-]+)$",
        "action": "remove_image",
        "description": "Menghapus sebuah image.",
        "example": "rm image nginx:latest"
    },
    {
        "id": "system_info",
        "pattern": r"^(?:sistem\s+info|system\s+info|docker\s+info)$",
        "action": "system_info",
        "description": "Menampilkan informasi sistem Docker (JSON).",
        "example": "docker info"
    },
    {
        "id": "system_version",
        "pattern": r"^(?:sistem\s+versi|system\s+version|docker\s+version)$",
        "action": "system_version",
        "description": "Menampilkan versi komponen Docker (JSON).",
        "example": "docker version"
    },
    {
        "id": "system_prune",
        "pattern": r"^(?:sistem\s+bersihkan|system\s+prune)$",
        "action": "prune_system",
        "description": "Membersihkan kontainer, image, volume, dan network yang tidak terpakai.",
        "example": "system prune"
    },
    {
        "id": "pause_container",
        "pattern": r"^(?:pause|jeda)\s+(?:(?:kontainer|container)\s+)?(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "pause_container",
        "description": "Menghentikan sementara (pause) sebuah kontainer.",
        "example": "pause webku"
    },
    {
        "id": "unpause_container",
        "pattern": r"^(?:unpause|lanjutkan)\s+(?:(?:kontainer|container)\s+)?(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "unpause_container",
        "description": "Melanjutkan kembali kontainer yang di-pause.",
        "example": "unpause webku"
    },
    {
        "id": "create_volume",
        "pattern": r"^(?:buat|create)\s+volume\s+(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "create_volume",
        "description": "Membuat volume Docker baru.",
        "example": "create volume data_baru"
    },
    {
        "id": "compose_ps",
        "pattern": r"^compose-?ps$",
        "action": "compose_ps",
        "description": "Menampilkan status kontainer dari docker-compose.",
        "example": "compose-ps"
    },
    {
        "id": "compose_logs",
        "pattern": r"^compose-?logs(?:\s+(?P<service>[a-zA-Z0-9_.-]+))?(?:\s+sebanyak\s+(?P<lines>\d+)\s+baris)?$",
        "action": "compose_logs",
        "description": "Menampilkan log dari service docker-compose.",
        "example": "compose-logs web_service sebanyak 100 baris"
    },
    {
        "id": "exec_in_container",
        "pattern": r"^(?:exec|jalankan\s+di)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+(?P<command>.+)$",
        "action": "exec_in_container",
        "description": "Menjalankan perintah di dalam kontainer yang sedang berjalan.",
        "example": "exec webku ls -l /var/www/html"
    },
    {
        "id": "rename_container",
        "pattern": r"^(?:rename|ganti nama)\s+(?:(?:kontainer|container)\s+)?(?P<old_name>[a-zA-Z0-9_.-]+)\s+(?:to|ke|menjadi)\s+(?P<new_name>[a-zA-Z0-9_.-]+)$",
        "action": "rename_container",
        "description": "Mengganti nama sebuah kontainer.",
        "example": "rename container web_lama ke web_baru"
    },
    {
        "id": "remove_network",
        "pattern": r"^(?:hapus|rm|remove)\s+network\s+(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "remove_network",
        "description": "Menghapus sebuah network.",
        "example": "rm network my_app_net"
    },
    {
        "id": "compose_restart",
        "pattern": r"^compose-?restart(?:\s+(?P<service>[a-zA-Z0-9_.-]+))?$",
        "action": "compose_restart",
        "description": "Me-restart service dari docker-compose.",
        "example": "compose-restart web_service"
    },
    {
        "id": "compose_build",
        "pattern": r"^compose-?build(?:\s+(?P<service>[a-zA-Z0-9_.-]+))?$",
        "action": "compose_build",
        "description": "Membangun (build) image untuk service docker-compose.",
        "example": "compose-build"
    }
]