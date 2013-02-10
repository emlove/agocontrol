#

.SUFFIXES:	.cpp .o .a .s

CC     := gcc
CXX    := g++
LD     := g++
AR     := ar rc
RANLIB := ranlib

DEBUG_CFLAGS    := -Wall -Werror -Wno-format -g -DDEBUG -fpic
RELEASE_CFLAGS  := -Wall -Wno-unknown-pragmas -Wno-format -O3
LIB_VER         := .1
DEBUG_LDFLAGS	:= -g -shared -Wl,-soname,libagoclient.so$(LIB_VER)

# Change for DEBUG or RELEASE
CFLAGS	:= -c $(DEBUG_CFLAGS)
LDFLAGS	:= $(DEBUG_LDFLAGS)

INCLUDES	:= 

%.o : %.cpp
	$(CXX) $(CFLAGS) $(INCLUDES) -o $@ $<

all: libagoclient.so

libagoclient.so: agoclient.o CDataFile.o
	$(LD) -o $(@)$(LIB_VER) $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -ljsoncpp
	ln -s $(@)$(LIB_VER) $(@)

clean:
	rm -f agoclient.o CDataFile.o libagoclient.so*
