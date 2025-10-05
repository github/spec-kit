import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_DeleteConfigurationSetEventDestinationCommand, se_DeleteConfigurationSetEventDestinationCommand, } from "../protocols/Aws_query";
export { $Command };
export class DeleteConfigurationSetEventDestinationCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "DeleteConfigurationSetEventDestination", {})
    .n("SESClient", "DeleteConfigurationSetEventDestinationCommand")
    .f(void 0, void 0)
    .ser(se_DeleteConfigurationSetEventDestinationCommand)
    .de(de_DeleteConfigurationSetEventDestinationCommand)
    .build() {
}
