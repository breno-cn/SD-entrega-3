#!/bin/bash

WAIT_FOR_IT() {
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
    node=$1
    bits=$2

    echo "spawning node $node"

    p1=$(echo $(($RANDOM % $MAX_PORT)))
    echo "p1 = $p1"

    p2=$(echo $(($RANDOM % $MAX_PORT)))
    echo "p2 = $p2"

    p3=$(echo $(($RANDOM % $MAX_PORT)))
    echo "p3 = $p3"

    python3 Server.py $node $bits $p1 $p2 $p3 &
    serverPid=$!
    serverPids[$i]=$serverPid
    i=$((i+1))

    python3 Server.py $node $bits $p2 $p1 $p3 &
    serverPid=$!
    serverPids[$i]=$serverPid
    i=$((i+1))

    python3 Server.py $node $bits $p3 $p1 $p2 &
    serverPid=$!
    serverPids[$i]=$serverPid
    i=$((i+1))
}

M=$1
serversNum=$2
maxNodes=$(echo "2^$M" | bc)

echo "Subirao $serversNum servidores numa rede que usara $M bits para a hash"

# OK
for j in $(seq 1 $serversNum); do
    N=$(echo $(($RANDOM % $maxNodes)))
    echo "node $N"

    spaw_node "$N" "$M"
done

WAIT_FOR_IT

echo "-------------------------------------"
echo "i = $i"
echo "serverPids = ${serverPids}"
echo "-------------------------------------"

# OK
WAIT_FOR_IT

for j in $(seq 0 $i); do
    kill -SIGUSR1 ${serverPids[$j]}
done

WAIT_FOR_IT

# OK
for j in $(seq 0 $i); do
    echo "Matando servidor de pid ${serverPids[$j]}"
    kill -9 ${serverPids[$j]}
done
