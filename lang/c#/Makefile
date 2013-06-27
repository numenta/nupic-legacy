

# Use expanded variables (:=) to evaluate once now rather than each time when referenced
netCPPFILES := $(wildcard ../../nta2/*/*.cpp)
netOBJFILES := $(patsubst %.cpp,%.o,$(netCPPFILES))
netHEADERFILES := $(patsubst %.cpp,%.hpp,$(netCPPFILES))

all: net_internal.so

clean:
	rm -f net_internal.so net_internal_wrap.cxx net_internal_wrap.o

net_internal.so: net_internal_wrap.o
	$(CXX) -Wl,-undefined -Wl,dynamic_lookup -shared net_internal_wrap.o $(netOBJFILES) -o net_internal.so -m32

# -Wno-format because generated swig code sometimes uses a printf-style function with no formatting string
net_internal_wrap.o: net_internal_wrap.cxx
	$(CC) -c -I../.. net_internal_wrap.cxx -DNTA_PLATFORM_darwin86 -m32 -Wno-format

net_internal_wrap.cxx: net_internal.i exception.i $(netHEADERFILES)
	swig  -c++ -csharp -namespace net_internal -DNTA_PLATFORM_darwin86 -DNTA_API_PUBLIC="" -I../.. net_internal.i
