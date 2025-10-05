import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_PutIdentityPolicyCommand, se_PutIdentityPolicyCommand } from "../protocols/Aws_query";
export { $Command };
export class PutIdentityPolicyCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "PutIdentityPolicy", {})
    .n("SESClient", "PutIdentityPolicyCommand")
    .f(void 0, void 0)
    .ser(se_PutIdentityPolicyCommand)
    .de(de_PutIdentityPolicyCommand)
    .build() {
}
