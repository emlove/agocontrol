#

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

INCLUDES	:= -I/usr/include/jsoncpp

%.o : %.cpp
	$(CXX) $(CFLAGS) $(INCLUDES) -o $@ $<

all: agorpc

agorpc: agorpc.o mongoose.o ../../devices/agozwave/CDataFile.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -ljsoncpp

clean:
	rm -f agorpc agorpc.o mongoose.o ../../devices/agozwave/CDataFile.o
