import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_UpdateTemplateCommand, se_UpdateTemplateCommand } from "../protocols/Aws_query";
export { $Command };
export class UpdateTemplateCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "UpdateTemplate", {})
    .n("SESClient", "UpdateTemplateCommand")
    .f(void 0, void 0)
    .ser(se_UpdateTemplateCommand)
    .de(de_UpdateTemplateCommand)
    .build() {
}
