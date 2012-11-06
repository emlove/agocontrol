#
# Makefile for OpenzWave Mac OS X applications
# Greg Satz

# GNU make only

# requires libudev-dev

.SUFFIXES:	.cpp .o .a .s

CC     := gcc
CXX    := g++
LD     := g++
AR     := ar rc
RANLIB := ranlib

DEBUG_CFLAGS    := -Wall -Wno-format -g -DDEBUG
RELEASE_CFLAGS  := -Wall -Wno-unknown-pragmas -Wno-format -O3

DEBUG_LDFLAGS	:= -g

# Change for DEBUG or RELEASE
CFLAGS	:= -c $(DEBUG_CFLAGS)
LDFLAGS	:= $(DEBUG_LDFLAGS)

INCLUDES	:= -I/usr/include/openzwave -I/usr/include/openzwave/value_classes -I/usr/include/openzwave/platform -I/usr/include/openzwave/platform/unix

%.o : %.cpp
	$(CXX) $(CFLAGS) $(INCLUDES) -o $@ $<

all: agozwave

agozwave: Main.o CDataFile.o
	$(LD) -o $@ $(LDFLAGS) $^ -pthread -ludev -lqpidmessaging -lqpidtypes -luuid -lopenzwave

clean:
	rm -f agozwave Main.o CDataFile.o
