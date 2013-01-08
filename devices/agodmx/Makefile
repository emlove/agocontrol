#

.SUFFIXES:      .cpp .o .a .s

CC     := gcc
CXX    := g++
LD     := g++
AR     := ar rc
RANLIB := ranlib

DEBUG_CFLAGS    := -Wall -Wno-format -g -DDEBUG -Werror
RELEASE_CFLAGS  := -Wall -Wno-unknown-pragmas -Wno-format -O3

DEBUG_LDFLAGS   := -g

# Change for DEBUG or RELEASE
CFLAGS  := -c $(DEBUG_CFLAGS)
LDFLAGS := $(DEBUG_LDFLAGS)

INCLUDES        :=

%.o : %.cpp
	$(CXX) $(CFLAGS) $(INCLUDES) -o $@ $<

all: agodmx


agodmx: agodmx.o ../agozwave/CDataFile.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -lola -ltinyxml2

clean:
	rm -f agodmx agodmx.o ../agozwave/CDataFile.o
