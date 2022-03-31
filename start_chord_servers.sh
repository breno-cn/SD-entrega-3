#!/bin/bash

WAIT_FOR_IT() {
    echo "Pressione qualquer tecla para matar os processos"
    while [ true ] ; do
        read -t 3 -n 1
        if [ $? = 0 ] ; then
            return ;
        else
            echo "..."
        fi
    done
}

declare -A serverPids
i=0
spaw_node() {
    MAX_PORT=99999
    N=$1

    echo "spawning node $N"

    p1=$(echo $(($RANDOM % $MAX_PORT)))
    p2=$(echo $(($RANDOM % $MAX_PORT)))
    p3=$(echo $(($RANDOM % $MAX_PORT)))

    python3 Server.py $N $M $p1 &
    serverPid=$!
    serverPids[$i]=$serverPid
    i=$((i+1))

    python3 Server.py $N $M $p2 &
    serverPid=$!
    serverPids[$i]=$serverPid
    i=$((i+1))

    python3 Server.py $N $M $p3 &
    serverPid=$!
    serverPids[$i]=$serverPid
    i=$((i+1))
}

M=$1
serversNum=$2
maxNodes=$(echo "2^$M" | bc)

echo "Subirao $serversNum servidores numa rede que usara $M bits para a hash"

for i in $(seq 1 $serversNum); do
    N=$(echo $(($RANDOM % $maxNodes)))
    echo "node $N"

    spaw_node "$N"
done

WAIT_FOR_IT

for j in $(seq 1 $i); do
    kill -SIGUSR1 ${serverPids[$j]}
done

WAIT_FOR_IT

for j in $(seq 1 $i); do
    echo "Matando servidor de pid ${serverPids[$j]}"
    kill -9 ${serverPids[$j]}
done
