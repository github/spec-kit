import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { SendTemplatedEmailRequest, SendTemplatedEmailResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link SendTemplatedEmailCommand}.
 */
export interface SendTemplatedEmailCommandInput extends SendTemplatedEmailRequest {
}
/**
 * @public
 *
 * The output of {@link SendTemplatedEmailCommand}.
 */
export interface SendTemplatedEmailCommandOutput extends SendTemplatedEmailResponse, __MetadataBearer {
}
declare const SendTemplatedEmailCommand_base: {
    new (input: SendTemplatedEmailCommandInput): import("@smithy/smithy-client").CommandImpl<SendTemplatedEmailCommandInput, SendTemplatedEmailCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: SendTemplatedEmailCommandInput): import("@smithy/smithy-client").CommandImpl<SendTemplatedEmailCommandInput, SendTemplatedEmailCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Composes an email message using an email template and immediately queues it for
 *             sending.</p>
 *          <p>To send email using this operation, your call must meet the following
 *             requirements:</p>
 *          <ul>
 *             <li>
 *                <p>The call must refer to an existing email template. You can create email
 *                     templates using the <a>CreateTemplate</a> operation.</p>
 *             </li>
 *             <li>
 *                <p>The message must be sent from a verified email address or domain.</p>
 *             </li>
 *             <li>
 *                <p>If your account is still in the Amazon SES sandbox, you may only send to verified
 *                     addresses or domains, or to email addresses associated with the Amazon SES Mailbox
 *                     Simulator. For more information, see <a href="https://docs.aws.amazon.com/ses/latest/dg/verify-addresses-and-domains.html">Verifying Email
 *                         Addresses and Domains</a> in the <i>Amazon SES Developer
 *                         Guide.</i>
 *                </p>
 *             </li>
 *             <li>
 *                <p>The maximum message size is 10 MB.</p>
 *             </li>
 *             <li>
 *                <p>Calls to the <code>SendTemplatedEmail</code> operation may only include one
 *                         <code>Destination</code> parameter. A destination is a set of recipients
 *                     that receives the same version of the email. The <code>Destination</code>
 *                     parameter can include up to 50 recipients, across the To:, CC: and BCC:
 *                     fields.</p>
 *             </li>
 *             <li>
 *                <p>The <code>Destination</code> parameter must include at least one recipient
 *                     email address. The recipient address can be a To: address, a CC: address, or a
 *                     BCC: address. If a recipient email address is invalid (that is, it is not in the
 *                     format <i>UserName@[SubDomain.]Domain.TopLevelDomain</i>), the
 *                     entire message is rejected, even if the message contains other recipients that
 *                     are valid.</p>
 *             </li>
 *          </ul>
 *          <important>
 *             <p>If your call to the <code>SendTemplatedEmail</code> operation includes all of the
 *                 required parameters, Amazon SES accepts it and returns a Message ID. However, if Amazon SES
 *                 can't render the email because the template contains errors, it doesn't send the
 *                 email. Additionally, because it already accepted the message, Amazon SES doesn't return a
 *                 message stating that it was unable to send the email.</p>
 *             <p>For these reasons, we highly recommend that you set up Amazon SES to send you
 *                 notifications when Rendering Failure events occur. For more information, see <a href="https://docs.aws.amazon.com/ses/latest/dg/send-personalized-email-api.html">Sending Personalized Email Using the Amazon SES API</a> in the
 *                     <i>Amazon Simple Email Service Developer Guide</i>.</p>
 *          </important>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, SendTemplatedEmailCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, SendTemplatedEmailCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // SendTemplatedEmailRequest
 *   Source: "STRING_VALUE", // required
 *   Destination: { // Destination
 *     ToAddresses: [ // AddressList
 *       "STRING_VALUE",
 *     ],
 *     CcAddresses: [
 *       "STRING_VALUE",
 *     ],
 *     BccAddresses: [
 *       "STRING_VALUE",
 *     ],
 *   },
 *   ReplyToAddresses: [
 *     "STRING_VALUE",
 *   ],
 *   ReturnPath: "STRING_VALUE",
 *   SourceArn: "STRING_VALUE",
 *   ReturnPathArn: "STRING_VALUE",
 *   Tags: [ // MessageTagList
 *     { // MessageTag
 *       Name: "STRING_VALUE", // required
 *       Value: "STRING_VALUE", // required
 *     },
 *   ],
 *   ConfigurationSetName: "STRING_VALUE",
 *   Template: "STRING_VALUE", // required
 *   TemplateArn: "STRING_VALUE",
 *   TemplateData: "STRING_VALUE", // required
 * };
 * const command = new SendTemplatedEmailCommand(input);
 * const response = await client.send(command);
 * // { // SendTemplatedEmailResponse
 * //   MessageId: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param SendTemplatedEmailCommandInput - {@link SendTemplatedEmailCommandInput}
 * @returns {@link SendTemplatedEmailCommandOutput}
 * @see {@link SendTemplatedEmailCommandInput} for command's `input` shape.
 * @see {@link SendTemplatedEmailCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link AccountSendingPausedException} (client fault)
 *  <p>Indicates that email sending is disabled for your entire Amazon SES account.</p>
 *          <p>You can enable or disable email sending for your Amazon SES account using <a>UpdateAccountSendingEnabled</a>.</p>
 *
 * @throws {@link ConfigurationSetDoesNotExistException} (client fault)
 *  <p>Indicates that the configuration set does not exist.</p>
 *
 * @throws {@link ConfigurationSetSendingPausedException} (client fault)
 *  <p>Indicates that email sending is disabled for the configuration set.</p>
 *          <p>You can enable or disable email sending for a configuration set using <a>UpdateConfigurationSetSendingEnabled</a>.</p>
 *
 * @throws {@link MailFromDomainNotVerifiedException} (client fault)
 *  <p> Indicates that the message could not be sent because Amazon SES could not read the MX
 *             record required to use the specified MAIL FROM domain. For information about editing the
 *             custom MAIL FROM domain settings for an identity, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/mail-from-edit.html">Amazon SES Developer
 *                 Guide</a>.</p>
 *
 * @throws {@link MessageRejected} (client fault)
 *  <p>Indicates that the action failed, and the message could not be sent. Check the error
 *             stack for more information about what caused the error.</p>
 *
 * @throws {@link TemplateDoesNotExistException} (client fault)
 *  <p>Indicates that the Template object you specified does not exist in your Amazon SES
 *             account.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class SendTemplatedEmailCommand extends SendTemplatedEmailCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: SendTemplatedEmailRequest;
            output: SendTemplatedEmailResponse;
        };
        sdk: {
            input: SendTemplatedEmailCommandInput;
            output: SendTemplatedEmailCommandOutput;
        };
    };
}
