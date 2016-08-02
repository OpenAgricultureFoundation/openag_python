from ..base import Plugin

class CSVCommPlugin(Plugin):
    def setup_plugin(self, f):
        f.writeln("Serial.begin(9600);")

    def update_plugin(self, f):
        # Read inputs from the serial port
        with f._if("Serial.available()"):
            f.writeln("String in_str = Serial.readString();")
            for mod_name, mod_info in self.modules.items():
                for input_name, input_info in mod_info["inputs"].items():
                    mapped_input_name = input_info["mapped_name"]
                    prefix="{},{},".format(mod_name, mapped_input_name)
                    with f._if('in_str.startsWith("{}")'.format(prefix)):
                        input_type = input_info["type"]
                        if input_type == "std_msgs/Bool":
                            f.writeln("std_msgs::Bool val;")
                            with f._if('in_str.endsWith("true")'):
                                f.writeln("val.data = true;");
                                f.writeln(
                                    "{mod_name}.set_{input_name}(val);".format(
                                        mod_name=mod_name,input_name=input_name
                                    )
                                )
                            with f._elif('in_str.endsWith("false")'):
                                f.writeln("val.data = false;")
                                f.writeln(
                                    "{mod_name}.set_{input_name}(val);".format(
                                        mod_name=mod_name,input_name=input_name
                                    )
                                )
                        else:
                            raise RuntimeException(
                                "CSV plugin doesn't support inputs of type " +
                                input_type
                            )

    def on_output(self, mod_name, output_name, f):
        real_output_name = self.modules[mod_name]["outputs"][output_name]["mapped_name"]
        f.writeln('Serial.print("data,{mod_name},{output_name},");'.format(
            mod_name=mod_name, output_name=real_output_name
        ))
        f.writeln('Serial.println({msg_name}.data);'.format(
            msg_name=self.msg_name(mod_name, output_name)
        ))

    def read_module_status(self, mod_name, f):
        f.writeln('Serial.print("status,{mod_name},");'.format(
            mod_name=mod_name
        ))
        f.writeln("Serial.print({mod_name}.status_level);".format(
            mod_name=mod_name
        ))
        f.writeln('Serial.print(",");')
        f.writeln("Serial.println({mod_name}.status_msg);".format(
            mod_name=mod_name
        ))
