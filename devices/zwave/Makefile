#

.SUFFIXES:	.cpp .o .a .s

CC     := gcc
CXX    := g++
LD     := g++
AR     := ar rc
RANLIB := ranlib

DEBUG_CFLAGS    := -Wall -Wno-format -g -DDEBUG
RELEASE_CFLAGS  := -Wall -Wno-unknown-pragmas -Wno-format -O3

DEBUG_LDFLAGS	:= -g -L../../shared

# Change for DEBUG or RELEASE
CFLAGS	:= -c $(DEBUG_CFLAGS)
LDFLAGS	:= $(DEBUG_LDFLAGS)

INCLUDES	:=  -I../../shared -I/usr/include/openzwave -I/usr/include/openzwave/value_classes -I/usr/include/openzwave/platform -I/usr/include/openzwave/platform/unix


%.o : %.cpp
	$(CXX) $(CFLAGS) $(INCLUDES) -o $@ $<

all: agozwave

agozwave: agozwave.o ZWaveNode.o
	$(LD) -o $@ $(LDFLAGS) $^ -lagoclient -lopenzwave -ludev

clean:
	rm -f agozwave agozwave.o
