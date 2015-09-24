@0x9b23d989c61ef9e5;

using import "/nupic/encoders/scalar.capnp".ScalarEncoderProto;

struct DateEncoderProto {
  name @0 :Text;
  seasonEncoder @1 :ScalarEncoderProto;
  dayOfWeekEncoder @2 :ScalarEncoderProto;
  weekendEncoder @3 :ScalarEncoderProto;
  customDaysEncoder @4 :ScalarEncoderProto;
  holidayEncoder @5 :ScalarEncoderProto;
  timeOfDayEncoder @6 :ScalarEncoderProto;
}
