import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_UpdateConfigurationSetTrackingOptionsCommand, se_UpdateConfigurationSetTrackingOptionsCommand, } from "../protocols/Aws_query";
export { $Command };
export class UpdateConfigurationSetTrackingOptionsCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "UpdateConfigurationSetTrackingOptions", {})
    .n("SESClient", "UpdateConfigurationSetTrackingOptionsCommand")
    .f(void 0, void 0)
    .ser(se_UpdateConfigurationSetTrackingOptionsCommand)
    .de(de_UpdateConfigurationSetTrackingOptionsCommand)
    .build() {
}
