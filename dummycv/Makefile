TARGET := libdummycv.so
SRCS := dummycv.cpp
OBJS := $(SRCS:%.cpp=%.o)
DEPS := $(SRCS:%.cpp=%.d)

CXX := g++
CXXFLAGS := -g -fPIC -Wall -Wextra
CPPFLAGS :=
LDFLAGS :=
LIBS :=

all: $(TARGET)

-include $(DEPS)

$(TARGET): $(OBJS)
	$(CXX) $(LDFLAGS) --shared -o $@ $^ $(LIBS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) -c -MMD -MP $<

clean:
	rm -f $(TARGET) $(OBJS) $(DEPS)
