@0xe3bd9d03217a6041;

using import "/nupic/frameworks/opf/model.capnp".ModelProto;

# Next ID: 5
struct PreviousValueModelProto {
    modelBase @0 :ModelProto;
    # List of field names
    fieldNames @1 :List(Text);
    # List of field types corresponding to fields in fieldNames
    fieldTypes @2 :List(Text);
    # The field from fieldNames which is to be predicted
    predictedField @3 :Text;
    # A list of steps for which a prediction is made
    predictionSteps @4 :List(UInt32);
}
