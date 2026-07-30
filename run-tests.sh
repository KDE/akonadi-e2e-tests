#! /usr/bin/bash
# SPDX-FileCopyrightText: Kevin Ottens <kevin.ottens@enioka.com>
# SPDX-License-Identifier: GPL-2.0-or-later

MAX_RERUN=5
PYTEST_ARGS="-n 4 tests/"

uv run pytest $PYTEST_ARGS

if [ "$?" == "0" ]; then
    exit 0
fi

rerun=1
while [ $rerun -le $MAX_RERUN ]; do

    echo ""
    echo "================================"
    echo "Had some test failures, rerun $rerun"
    echo "================================"
    echo ""

    uv run pytest --lf $PYTEST_ARGS
    if [ "$?" == "0" ]; then
        exit 0
    fi

    ((rerun = rerun + 1))
done

# We had only failures bailing out
echo "All reruns failed! ;-("
exit 1
