import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { SendEmailRequest, SendEmailResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link SendEmailCommand}.
 */
export interface SendEmailCommandInput extends SendEmailRequest {
}
/**
 * @public
 *
 * The output of {@link SendEmailCommand}.
 */
export interface SendEmailCommandOutput extends SendEmailResponse, __MetadataBearer {
}
declare const SendEmailCommand_base: {
    new (input: SendEmailCommandInput): import("@smithy/smithy-client").CommandImpl<SendEmailCommandInput, SendEmailCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: SendEmailCommandInput): import("@smithy/smithy-client").CommandImpl<SendEmailCommandInput, SendEmailCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Composes an email message and immediately queues it for sending. To send email using
 *             this operation, your message must meet the following requirements:</p>
 *          <ul>
 *             <li>
 *                <p>The message must be sent from a verified email address or domain. If you
 *                     attempt to send email using a non-verified address or domain, the operation
 *                     results in an "Email address not verified" error. </p>
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
 *                <p>The message must include at least one recipient email address. The recipient
 *                     address can be a To: address, a CC: address, or a BCC: address. If a recipient
 *                     email address is invalid (that is, it is not in the format
 *                         <i>UserName@[SubDomain.]Domain.TopLevelDomain</i>), the entire
 *                     message is rejected, even if the message contains other recipients that are
 *                     valid.</p>
 *             </li>
 *             <li>
 *                <p>The message may not include more than 50 recipients, across the To:, CC: and
 *                     BCC: fields. If you need to send an email message to a larger audience, you can
 *                     divide your recipient list into groups of 50 or fewer, and then call the
 *                         <code>SendEmail</code> operation several times to send the message to each
 *                     group.</p>
 *             </li>
 *          </ul>
 *          <important>
 *             <p>For every message that you send, the total number of recipients (including each
 *                 recipient in the To:, CC: and BCC: fields) is counted against the maximum number of
 *                 emails you can send in a 24-hour period (your <i>sending quota</i>).
 *                 For more information about sending quotas in Amazon SES, see <a href="https://docs.aws.amazon.com/ses/latest/dg/manage-sending-quotas.html">Managing Your Amazon SES Sending
 *                     Limits</a> in the <i>Amazon SES Developer Guide.</i>
 *             </p>
 *          </important>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, SendEmailCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, SendEmailCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // SendEmailRequest
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
 *   Message: { // Message
 *     Subject: { // Content
 *       Data: "STRING_VALUE", // required
 *       Charset: "STRING_VALUE",
 *     },
 *     Body: { // Body
 *       Text: {
 *         Data: "STRING_VALUE", // required
 *         Charset: "STRING_VALUE",
 *       },
 *       Html: {
 *         Data: "STRING_VALUE", // required
 *         Charset: "STRING_VALUE",
 *       },
 *     },
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
 * };
 * const command = new SendEmailCommand(input);
 * const response = await client.send(command);
 * // { // SendEmailResponse
 * //   MessageId: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param SendEmailCommandInput - {@link SendEmailCommandInput}
 * @returns {@link SendEmailCommandOutput}
 * @see {@link SendEmailCommandInput} for command's `input` shape.
 * @see {@link SendEmailCommandOutput} for command's `response` shape.
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
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example SendEmail
 * ```javascript
 * // The following example sends a formatted email:
 * const input = {
 *   Destination: {
 *     BccAddresses:     [],
 *     CcAddresses: [
 *       "recipient3@example.com"
 *     ],
 *     ToAddresses: [
 *       "recipient1@example.com",
 *       "recipient2@example.com"
 *     ]
 *   },
 *   Message: {
 *     Body: {
 *       Html: {
 *         Charset: "UTF-8",
 *         Data: `This message body contains HTML formatting. It can, for example, contain links like this one: <a class="ulink" href="http://docs.aws.amazon.com/ses/latest/DeveloperGuide" target="_blank">Amazon SES Developer Guide</a>.`
 *       },
 *       Text: {
 *         Charset: "UTF-8",
 *         Data: "This is the message body in text format."
 *       }
 *     },
 *     Subject: {
 *       Charset: "UTF-8",
 *       Data: "Test email"
 *     }
 *   },
 *   ReplyToAddresses:   [],
 *   ReturnPath: "",
 *   ReturnPathArn: "",
 *   Source: "sender@example.com",
 *   SourceArn: ""
 * };
 * const command = new SendEmailCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   MessageId: "EXAMPLE78603177f-7a5433e7-8edb-42ae-af10-f0181f34d6ee-000000"
 * }
 * *\/
 * ```
 *
 * @public
 */
export declare class SendEmailCommand extends SendEmailCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: SendEmailRequest;
            output: SendEmailResponse;
        };
        sdk: {
            input: SendEmailCommandInput;
            output: SendEmailCommandOutput;
        };
    };
}
