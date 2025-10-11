import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_GetIdentityNotificationAttributesCommand, se_GetIdentityNotificationAttributesCommand, } from "../protocols/Aws_query";
export { $Command };
export class GetIdentityNotificationAttributesCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "GetIdentityNotificationAttributes", {})
    .n("SESClient", "GetIdentityNotificationAttributesCommand")
    .f(void 0, void 0)
    .ser(se_GetIdentityNotificationAttributesCommand)
    .de(de_GetIdentityNotificationAttributesCommand)
    .build() {
}
