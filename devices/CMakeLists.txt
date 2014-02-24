cmake_minimum_required (VERSION 2.6)

set (AGODEVICES
  enocean3
#  blinkm
#  chromoflex
  firmata
#  i2c
#  irtrans_ethernet
#  kwikwai
#  mediaproxy
#  rain8net
#  zwave
#  1wire
#  syslog
#  enigma2
#  asterisk
#  agoapc
#  agojointspace
#  raspiGPIO
#  raspi1wGPIO
  raspiMCP3xxxGPIO
  gc100
#  onkyo
#  x10
#  webcam
#  temperatur.nu
#  wake_on_lan
#  squeezebox
#  alert
#  ipx800
#  raspiCamera
#  scheduler
#  knx
  agodmx
)

foreach (device ${AGODEVICES})

    # options what to build
    OPTION(BUILD_DEVICE_${device} "Build the device ${device}" ON)
    if (BUILD_DEVICE_${device})
        add_subdirectory(${device})
    endif()

endforeach(device)
