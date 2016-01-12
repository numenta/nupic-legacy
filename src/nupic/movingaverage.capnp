@0xe712075e01db76d0;

# Next ID: 3
struct MovingAverageProto {
  windowSize @0 :UInt32;
  slidingWindow @1 :List(Float32);
  total @2 :Float32;
}
