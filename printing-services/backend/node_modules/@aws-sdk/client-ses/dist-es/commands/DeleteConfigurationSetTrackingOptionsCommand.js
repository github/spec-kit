import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_DeleteConfigurationSetTrackingOptionsCommand, se_DeleteConfigurationSetTrackingOptionsCommand, } from "../protocols/Aws_query";
export { $Command };
export class DeleteConfigurationSetTrackingOptionsCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "DeleteConfigurationSetTrackingOptions", {})
    .n("SESClient", "DeleteConfigurationSetTrackingOptionsCommand")
    .f(void 0, void 0)
    .ser(se_DeleteConfigurationSetTrackingOptionsCommand)
    .de(de_DeleteConfigurationSetTrackingOptionsCommand)
    .build() {
}
