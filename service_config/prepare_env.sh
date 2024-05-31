#!/bin/bash
if [ -z "CUSTOM_HEADER_LORIS" ]
then
    echo "CUSTOM_HEADER_LORIS is not set. Exiting."
    exit 2
else
    sed -i "s/CUSTOM_HEADER_LORIS/${CUSTOM_HEADER_LORIS}/g" ./service_config/files/env
    if [ `grep -c "CUSTOM_HEADER_LORIS" ./service_config/files/env` -ne 0 ]
    then
        echo "CUSTOM_HEADER_LORIS was not successfully replaced. Exiting."
        exit 2
    else
        echo "CUSTOM_HEADER_LORIS was successfully replaced."
        exit 0
    fi
fi
