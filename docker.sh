#!/bin/bash

IMAGE_NAME="audithunter"
CONTAINER_NAME="AuditHunterContainer"

build_and_run() {
    docker build -t $IMAGE_NAME .
    docker rm -f $CONTAINER_NAME 2>/dev/null
    docker run -d --name $CONTAINER_NAME $IMAGE_NAME
    docker ps -a
    docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' AuditHunterContainer

}

run_only() {
    docker rm -f $CONTAINER_NAME 2>/dev/null
    docker run -d --name $CONTAINER_NAME $IMAGE_NAME
}

run_bash() {
    python3 -m venv myenv
    source myenv/bin/activate
    pip install -r requirements.txt
    python3 app.py
}

run_rebash() {
    rm myenv -rf
    rm app.db
    rm audithunter.key.pem
    rm audithunter.cert.pem
    openssl req -x509 -newkey rsa:4096 -nodes -keyout audithunter.key.pem -out audithunter.cert.pem -days 365
    python3 -m venv myenv
    source myenv/bin/activate
    pip install -r requirements.txt
    python3 init_db.py
    python3 import_Adrela.py 
    python3 app.py
}
show_logs() {
    docker logs -f $CONTAINER_NAME
}

echo "=== Build & Run initial ==="

while true; do
    echo ""
    echo "Choix :"
    echo "re → rebuild + relancer"
    echo "log → afficher les logs"
    echo "bash → direct sur la machine"
    echo "reb → rebuild sur la machine"
    echo "run → relancer sans rebuild"
    echo "q → quitter"
    read -r choice

    case $choice in
        re)
            echo "Rebuild en cours..."
            build_and_run
            ;;
        log)
            echo "Logs du container :"
            show_logs
            ;;
        run)
            echo "Relance sans rebuild..."
            run_only
            ;;
        bash)
            echo "Bash lancé..."
            run_bash
            ;;
        reb)
            echo "Bash lancé..."
            run_rebash
            ;;
        q)
            echo "Arrêt."
            exit 0
            ;;
        *)
            echo "Commande inconnue"
            ;;
    esac
done
