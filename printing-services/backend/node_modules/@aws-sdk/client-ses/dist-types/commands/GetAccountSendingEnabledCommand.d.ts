import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { GetAccountSendingEnabledResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetAccountSendingEnabledCommand}.
 */
export interface GetAccountSendingEnabledCommandInput {
}
/**
 * @public
 *
 * The output of {@link GetAccountSendingEnabledCommand}.
 */
export interface GetAccountSendingEnabledCommandOutput extends GetAccountSendingEnabledResponse, __MetadataBearer {
}
declare const GetAccountSendingEnabledCommand_base: {
    new (input: GetAccountSendingEnabledCommandInput): import("@smithy/smithy-client").CommandImpl<GetAccountSendingEnabledCommandInput, GetAccountSendingEnabledCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (...[input]: [] | [GetAccountSendingEnabledCommandInput]): import("@smithy/smithy-client").CommandImpl<GetAccountSendingEnabledCommandInput, GetAccountSendingEnabledCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Returns the email sending status of the Amazon SES account for the current Region.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, GetAccountSendingEnabledCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, GetAccountSendingEnabledCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = {};
 * const command = new GetAccountSendingEnabledCommand(input);
 * const response = await client.send(command);
 * // { // GetAccountSendingEnabledResponse
 * //   Enabled: true || false,
 * // };
 *
 * ```
 *
 * @param GetAccountSendingEnabledCommandInput - {@link GetAccountSendingEnabledCommandInput}
 * @returns {@link GetAccountSendingEnabledCommandOutput}
 * @see {@link GetAccountSendingEnabledCommandInput} for command's `input` shape.
 * @see {@link GetAccountSendingEnabledCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example GetAccountSendingEnabled
 * ```javascript
 * // The following example returns if sending status for an account is enabled. (true / false):
 * const input = { /* empty *\/ };
 * const command = new GetAccountSendingEnabledCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   Enabled: true
 * }
 * *\/
 * ```
 *
 * @public
 */
export declare class GetAccountSendingEnabledCommand extends GetAccountSendingEnabledCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: {};
            output: GetAccountSendingEnabledResponse;
        };
        sdk: {
            input: GetAccountSendingEnabledCommandInput;
            output: GetAccountSendingEnabledCommandOutput;
        };
    };
}
