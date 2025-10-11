import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_GetIdentityDkimAttributesCommand, se_GetIdentityDkimAttributesCommand } from "../protocols/Aws_query";
export { $Command };
export class GetIdentityDkimAttributesCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "GetIdentityDkimAttributes", {})
    .n("SESClient", "GetIdentityDkimAttributesCommand")
    .f(void 0, void 0)
    .ser(se_GetIdentityDkimAttributesCommand)
    .de(de_GetIdentityDkimAttributesCommand)
    .build() {
}
