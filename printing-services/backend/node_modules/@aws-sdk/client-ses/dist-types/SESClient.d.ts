import { HostHeaderInputConfig, HostHeaderResolvedConfig } from "@aws-sdk/middleware-host-header";
import { UserAgentInputConfig, UserAgentResolvedConfig } from "@aws-sdk/middleware-user-agent";
import { RegionInputConfig, RegionResolvedConfig } from "@smithy/config-resolver";
import { EndpointInputConfig, EndpointResolvedConfig } from "@smithy/middleware-endpoint";
import { RetryInputConfig, RetryResolvedConfig } from "@smithy/middleware-retry";
import { HttpHandlerUserInput as __HttpHandlerUserInput } from "@smithy/protocol-http";
import { Client as __Client, DefaultsMode as __DefaultsMode, SmithyConfiguration as __SmithyConfiguration, SmithyResolvedConfiguration as __SmithyResolvedConfiguration } from "@smithy/smithy-client";
import { AwsCredentialIdentityProvider, BodyLengthCalculator as __BodyLengthCalculator, CheckOptionalClientConfig as __CheckOptionalClientConfig, ChecksumConstructor as __ChecksumConstructor, Decoder as __Decoder, Encoder as __Encoder, HashConstructor as __HashConstructor, HttpHandlerOptions as __HttpHandlerOptions, Logger as __Logger, Provider as __Provider, Provider, StreamCollector as __StreamCollector, UrlParser as __UrlParser, UserAgent as __UserAgent } from "@smithy/types";
import { HttpAuthSchemeInputConfig, HttpAuthSchemeResolvedConfig } from "./auth/httpAuthSchemeProvider";
import { CloneReceiptRuleSetCommandInput, CloneReceiptRuleSetCommandOutput } from "./commands/CloneReceiptRuleSetCommand";
import { CreateConfigurationSetCommandInput, CreateConfigurationSetCommandOutput } from "./commands/CreateConfigurationSetCommand";
import { CreateConfigurationSetEventDestinationCommandInput, CreateConfigurationSetEventDestinationCommandOutput } from "./commands/CreateConfigurationSetEventDestinationCommand";
import { CreateConfigurationSetTrackingOptionsCommandInput, CreateConfigurationSetTrackingOptionsCommandOutput } from "./commands/CreateConfigurationSetTrackingOptionsCommand";
import { CreateCustomVerificationEmailTemplateCommandInput, CreateCustomVerificationEmailTemplateCommandOutput } from "./commands/CreateCustomVerificationEmailTemplateCommand";
import { CreateReceiptFilterCommandInput, CreateReceiptFilterCommandOutput } from "./commands/CreateReceiptFilterCommand";
import { CreateReceiptRuleCommandInput, CreateReceiptRuleCommandOutput } from "./commands/CreateReceiptRuleCommand";
import { CreateReceiptRuleSetCommandInput, CreateReceiptRuleSetCommandOutput } from "./commands/CreateReceiptRuleSetCommand";
import { CreateTemplateCommandInput, CreateTemplateCommandOutput } from "./commands/CreateTemplateCommand";
import { DeleteConfigurationSetCommandInput, DeleteConfigurationSetCommandOutput } from "./commands/DeleteConfigurationSetCommand";
import { DeleteConfigurationSetEventDestinationCommandInput, DeleteConfigurationSetEventDestinationCommandOutput } from "./commands/DeleteConfigurationSetEventDestinationCommand";
import { DeleteConfigurationSetTrackingOptionsCommandInput, DeleteConfigurationSetTrackingOptionsCommandOutput } from "./commands/DeleteConfigurationSetTrackingOptionsCommand";
import { DeleteCustomVerificationEmailTemplateCommandInput, DeleteCustomVerificationEmailTemplateCommandOutput } from "./commands/DeleteCustomVerificationEmailTemplateCommand";
import { DeleteIdentityCommandInput, DeleteIdentityCommandOutput } from "./commands/DeleteIdentityCommand";
import { DeleteIdentityPolicyCommandInput, DeleteIdentityPolicyCommandOutput } from "./commands/DeleteIdentityPolicyCommand";
import { DeleteReceiptFilterCommandInput, DeleteReceiptFilterCommandOutput } from "./commands/DeleteReceiptFilterCommand";
import { DeleteReceiptRuleCommandInput, DeleteReceiptRuleCommandOutput } from "./commands/DeleteReceiptRuleCommand";
import { DeleteReceiptRuleSetCommandInput, DeleteReceiptRuleSetCommandOutput } from "./commands/DeleteReceiptRuleSetCommand";
import { DeleteTemplateCommandInput, DeleteTemplateCommandOutput } from "./commands/DeleteTemplateCommand";
import { DeleteVerifiedEmailAddressCommandInput, DeleteVerifiedEmailAddressCommandOutput } from "./commands/DeleteVerifiedEmailAddressCommand";
import { DescribeActiveReceiptRuleSetCommandInput, DescribeActiveReceiptRuleSetCommandOutput } from "./commands/DescribeActiveReceiptRuleSetCommand";
import { DescribeConfigurationSetCommandInput, DescribeConfigurationSetCommandOutput } from "./commands/DescribeConfigurationSetCommand";
import { DescribeReceiptRuleCommandInput, DescribeReceiptRuleCommandOutput } from "./commands/DescribeReceiptRuleCommand";
import { DescribeReceiptRuleSetCommandInput, DescribeReceiptRuleSetCommandOutput } from "./commands/DescribeReceiptRuleSetCommand";
import { GetAccountSendingEnabledCommandInput, GetAccountSendingEnabledCommandOutput } from "./commands/GetAccountSendingEnabledCommand";
import { GetCustomVerificationEmailTemplateCommandInput, GetCustomVerificationEmailTemplateCommandOutput } from "./commands/GetCustomVerificationEmailTemplateCommand";
import { GetIdentityDkimAttributesCommandInput, GetIdentityDkimAttributesCommandOutput } from "./commands/GetIdentityDkimAttributesCommand";
import { GetIdentityMailFromDomainAttributesCommandInput, GetIdentityMailFromDomainAttributesCommandOutput } from "./commands/GetIdentityMailFromDomainAttributesCommand";
import { GetIdentityNotificationAttributesCommandInput, GetIdentityNotificationAttributesCommandOutput } from "./commands/GetIdentityNotificationAttributesCommand";
import { GetIdentityPoliciesCommandInput, GetIdentityPoliciesCommandOutput } from "./commands/GetIdentityPoliciesCommand";
import { GetIdentityVerificationAttributesCommandInput, GetIdentityVerificationAttributesCommandOutput } from "./commands/GetIdentityVerificationAttributesCommand";
import { GetSendQuotaCommandInput, GetSendQuotaCommandOutput } from "./commands/GetSendQuotaCommand";
import { GetSendStatisticsCommandInput, GetSendStatisticsCommandOutput } from "./commands/GetSendStatisticsCommand";
import { GetTemplateCommandInput, GetTemplateCommandOutput } from "./commands/GetTemplateCommand";
import { ListConfigurationSetsCommandInput, ListConfigurationSetsCommandOutput } from "./commands/ListConfigurationSetsCommand";
import { ListCustomVerificationEmailTemplatesCommandInput, ListCustomVerificationEmailTemplatesCommandOutput } from "./commands/ListCustomVerificationEmailTemplatesCommand";
import { ListIdentitiesCommandInput, ListIdentitiesCommandOutput } from "./commands/ListIdentitiesCommand";
import { ListIdentityPoliciesCommandInput, ListIdentityPoliciesCommandOutput } from "./commands/ListIdentityPoliciesCommand";
import { ListReceiptFiltersCommandInput, ListReceiptFiltersCommandOutput } from "./commands/ListReceiptFiltersCommand";
import { ListReceiptRuleSetsCommandInput, ListReceiptRuleSetsCommandOutput } from "./commands/ListReceiptRuleSetsCommand";
import { ListTemplatesCommandInput, ListTemplatesCommandOutput } from "./commands/ListTemplatesCommand";
import { ListVerifiedEmailAddressesCommandInput, ListVerifiedEmailAddressesCommandOutput } from "./commands/ListVerifiedEmailAddressesCommand";
import { PutConfigurationSetDeliveryOptionsCommandInput, PutConfigurationSetDeliveryOptionsCommandOutput } from "./commands/PutConfigurationSetDeliveryOptionsCommand";
import { PutIdentityPolicyCommandInput, PutIdentityPolicyCommandOutput } from "./commands/PutIdentityPolicyCommand";
import { ReorderReceiptRuleSetCommandInput, ReorderReceiptRuleSetCommandOutput } from "./commands/ReorderReceiptRuleSetCommand";
import { SendBounceCommandInput, SendBounceCommandOutput } from "./commands/SendBounceCommand";
import { SendBulkTemplatedEmailCommandInput, SendBulkTemplatedEmailCommandOutput } from "./commands/SendBulkTemplatedEmailCommand";
import { SendCustomVerificationEmailCommandInput, SendCustomVerificationEmailCommandOutput } from "./commands/SendCustomVerificationEmailCommand";
import { SendEmailCommandInput, SendEmailCommandOutput } from "./commands/SendEmailCommand";
import { SendRawEmailCommandInput, SendRawEmailCommandOutput } from "./commands/SendRawEmailCommand";
import { SendTemplatedEmailCommandInput, SendTemplatedEmailCommandOutput } from "./commands/SendTemplatedEmailCommand";
import { SetActiveReceiptRuleSetCommandInput, SetActiveReceiptRuleSetCommandOutput } from "./commands/SetActiveReceiptRuleSetCommand";
import { SetIdentityDkimEnabledCommandInput, SetIdentityDkimEnabledCommandOutput } from "./commands/SetIdentityDkimEnabledCommand";
import { SetIdentityFeedbackForwardingEnabledCommandInput, SetIdentityFeedbackForwardingEnabledCommandOutput } from "./commands/SetIdentityFeedbackForwardingEnabledCommand";
import { SetIdentityHeadersInNotificationsEnabledCommandInput, SetIdentityHeadersInNotificationsEnabledCommandOutput } from "./commands/SetIdentityHeadersInNotificationsEnabledCommand";
import { SetIdentityMailFromDomainCommandInput, SetIdentityMailFromDomainCommandOutput } from "./commands/SetIdentityMailFromDomainCommand";
import { SetIdentityNotificationTopicCommandInput, SetIdentityNotificationTopicCommandOutput } from "./commands/SetIdentityNotificationTopicCommand";
import { SetReceiptRulePositionCommandInput, SetReceiptRulePositionCommandOutput } from "./commands/SetReceiptRulePositionCommand";
import { TestRenderTemplateCommandInput, TestRenderTemplateCommandOutput } from "./commands/TestRenderTemplateCommand";
import { UpdateAccountSendingEnabledCommandInput, UpdateAccountSendingEnabledCommandOutput } from "./commands/UpdateAccountSendingEnabledCommand";
import { UpdateConfigurationSetEventDestinationCommandInput, UpdateConfigurationSetEventDestinationCommandOutput } from "./commands/UpdateConfigurationSetEventDestinationCommand";
import { UpdateConfigurationSetReputationMetricsEnabledCommandInput, UpdateConfigurationSetReputationMetricsEnabledCommandOutput } from "./commands/UpdateConfigurationSetReputationMetricsEnabledCommand";
import { UpdateConfigurationSetSendingEnabledCommandInput, UpdateConfigurationSetSendingEnabledCommandOutput } from "./commands/UpdateConfigurationSetSendingEnabledCommand";
import { UpdateConfigurationSetTrackingOptionsCommandInput, UpdateConfigurationSetTrackingOptionsCommandOutput } from "./commands/UpdateConfigurationSetTrackingOptionsCommand";
import { UpdateCustomVerificationEmailTemplateCommandInput, UpdateCustomVerificationEmailTemplateCommandOutput } from "./commands/UpdateCustomVerificationEmailTemplateCommand";
import { UpdateReceiptRuleCommandInput, UpdateReceiptRuleCommandOutput } from "./commands/UpdateReceiptRuleCommand";
import { UpdateTemplateCommandInput, UpdateTemplateCommandOutput } from "./commands/UpdateTemplateCommand";
import { VerifyDomainDkimCommandInput, VerifyDomainDkimCommandOutput } from "./commands/VerifyDomainDkimCommand";
import { VerifyDomainIdentityCommandInput, VerifyDomainIdentityCommandOutput } from "./commands/VerifyDomainIdentityCommand";
import { VerifyEmailAddressCommandInput, VerifyEmailAddressCommandOutput } from "./commands/VerifyEmailAddressCommand";
import { VerifyEmailIdentityCommandInput, VerifyEmailIdentityCommandOutput } from "./commands/VerifyEmailIdentityCommand";
import { ClientInputEndpointParameters, ClientResolvedEndpointParameters, EndpointParameters } from "./endpoint/EndpointParameters";
import { RuntimeExtension, RuntimeExtensionsConfig } from "./runtimeExtensions";
export { __Client };
/**
 * @public
 */
export type ServiceInputTypes = CloneReceiptRuleSetCommandInput | CreateConfigurationSetCommandInput | CreateConfigurationSetEventDestinationCommandInput | CreateConfigurationSetTrackingOptionsCommandInput | CreateCustomVerificationEmailTemplateCommandInput | CreateReceiptFilterCommandInput | CreateReceiptRuleCommandInput | CreateReceiptRuleSetCommandInput | CreateTemplateCommandInput | DeleteConfigurationSetCommandInput | DeleteConfigurationSetEventDestinationCommandInput | DeleteConfigurationSetTrackingOptionsCommandInput | DeleteCustomVerificationEmailTemplateCommandInput | DeleteIdentityCommandInput | DeleteIdentityPolicyCommandInput | DeleteReceiptFilterCommandInput | DeleteReceiptRuleCommandInput | DeleteReceiptRuleSetCommandInput | DeleteTemplateCommandInput | DeleteVerifiedEmailAddressCommandInput | DescribeActiveReceiptRuleSetCommandInput | DescribeConfigurationSetCommandInput | DescribeReceiptRuleCommandInput | DescribeReceiptRuleSetCommandInput | GetAccountSendingEnabledCommandInput | GetCustomVerificationEmailTemplateCommandInput | GetIdentityDkimAttributesCommandInput | GetIdentityMailFromDomainAttributesCommandInput | GetIdentityNotificationAttributesCommandInput | GetIdentityPoliciesCommandInput | GetIdentityVerificationAttributesCommandInput | GetSendQuotaCommandInput | GetSendStatisticsCommandInput | GetTemplateCommandInput | ListConfigurationSetsCommandInput | ListCustomVerificationEmailTemplatesCommandInput | ListIdentitiesCommandInput | ListIdentityPoliciesCommandInput | ListReceiptFiltersCommandInput | ListReceiptRuleSetsCommandInput | ListTemplatesCommandInput | ListVerifiedEmailAddressesCommandInput | PutConfigurationSetDeliveryOptionsCommandInput | PutIdentityPolicyCommandInput | ReorderReceiptRuleSetCommandInput | SendBounceCommandInput | SendBulkTemplatedEmailCommandInput | SendCustomVerificationEmailCommandInput | SendEmailCommandInput | SendRawEmailCommandInput | SendTemplatedEmailCommandInput | SetActiveReceiptRuleSetCommandInput | SetIdentityDkimEnabledCommandInput | SetIdentityFeedbackForwardingEnabledCommandInput | SetIdentityHeadersInNotificationsEnabledCommandInput | SetIdentityMailFromDomainCommandInput | SetIdentityNotificationTopicCommandInput | SetReceiptRulePositionCommandInput | TestRenderTemplateCommandInput | UpdateAccountSendingEnabledCommandInput | UpdateConfigurationSetEventDestinationCommandInput | UpdateConfigurationSetReputationMetricsEnabledCommandInput | UpdateConfigurationSetSendingEnabledCommandInput | UpdateConfigurationSetTrackingOptionsCommandInput | UpdateCustomVerificationEmailTemplateCommandInput | UpdateReceiptRuleCommandInput | UpdateTemplateCommandInput | VerifyDomainDkimCommandInput | VerifyDomainIdentityCommandInput | VerifyEmailAddressCommandInput | VerifyEmailIdentityCommandInput;
/**
 * @public
 */
export type ServiceOutputTypes = CloneReceiptRuleSetCommandOutput | CreateConfigurationSetCommandOutput | CreateConfigurationSetEventDestinationCommandOutput | CreateConfigurationSetTrackingOptionsCommandOutput | CreateCustomVerificationEmailTemplateCommandOutput | CreateReceiptFilterCommandOutput | CreateReceiptRuleCommandOutput | CreateReceiptRuleSetCommandOutput | CreateTemplateCommandOutput | DeleteConfigurationSetCommandOutput | DeleteConfigurationSetEventDestinationCommandOutput | DeleteConfigurationSetTrackingOptionsCommandOutput | DeleteCustomVerificationEmailTemplateCommandOutput | DeleteIdentityCommandOutput | DeleteIdentityPolicyCommandOutput | DeleteReceiptFilterCommandOutput | DeleteReceiptRuleCommandOutput | DeleteReceiptRuleSetCommandOutput | DeleteTemplateCommandOutput | DeleteVerifiedEmailAddressCommandOutput | DescribeActiveReceiptRuleSetCommandOutput | DescribeConfigurationSetCommandOutput | DescribeReceiptRuleCommandOutput | DescribeReceiptRuleSetCommandOutput | GetAccountSendingEnabledCommandOutput | GetCustomVerificationEmailTemplateCommandOutput | GetIdentityDkimAttributesCommandOutput | GetIdentityMailFromDomainAttributesCommandOutput | GetIdentityNotificationAttributesCommandOutput | GetIdentityPoliciesCommandOutput | GetIdentityVerificationAttributesCommandOutput | GetSendQuotaCommandOutput | GetSendStatisticsCommandOutput | GetTemplateCommandOutput | ListConfigurationSetsCommandOutput | ListCustomVerificationEmailTemplatesCommandOutput | ListIdentitiesCommandOutput | ListIdentityPoliciesCommandOutput | ListReceiptFiltersCommandOutput | ListReceiptRuleSetsCommandOutput | ListTemplatesCommandOutput | ListVerifiedEmailAddressesCommandOutput | PutConfigurationSetDeliveryOptionsCommandOutput | PutIdentityPolicyCommandOutput | ReorderReceiptRuleSetCommandOutput | SendBounceCommandOutput | SendBulkTemplatedEmailCommandOutput | SendCustomVerificationEmailCommandOutput | SendEmailCommandOutput | SendRawEmailCommandOutput | SendTemplatedEmailCommandOutput | SetActiveReceiptRuleSetCommandOutput | SetIdentityDkimEnabledCommandOutput | SetIdentityFeedbackForwardingEnabledCommandOutput | SetIdentityHeadersInNotificationsEnabledCommandOutput | SetIdentityMailFromDomainCommandOutput | SetIdentityNotificationTopicCommandOutput | SetReceiptRulePositionCommandOutput | TestRenderTemplateCommandOutput | UpdateAccountSendingEnabledCommandOutput | UpdateConfigurationSetEventDestinationCommandOutput | UpdateConfigurationSetReputationMetricsEnabledCommandOutput | UpdateConfigurationSetSendingEnabledCommandOutput | UpdateConfigurationSetTrackingOptionsCommandOutput | UpdateCustomVerificationEmailTemplateCommandOutput | UpdateReceiptRuleCommandOutput | UpdateTemplateCommandOutput | VerifyDomainDkimCommandOutput | VerifyDomainIdentityCommandOutput | VerifyEmailAddressCommandOutput | VerifyEmailIdentityCommandOutput;
/**
 * @public
 */
export interface ClientDefaults extends Partial<__SmithyConfiguration<__HttpHandlerOptions>> {
    /**
     * The HTTP handler to use or its constructor options. Fetch in browser and Https in Nodejs.
     */
    requestHandler?: __HttpHandlerUserInput;
    /**
     * A constructor for a class implementing the {@link @smithy/types#ChecksumConstructor} interface
     * that computes the SHA-256 HMAC or checksum of a string or binary buffer.
     * @internal
     */
    sha256?: __ChecksumConstructor | __HashConstructor;
    /**
     * The function that will be used to convert strings into HTTP endpoints.
     * @internal
     */
    urlParser?: __UrlParser;
    /**
     * A function that can calculate the length of a request body.
     * @internal
     */
    bodyLengthChecker?: __BodyLengthCalculator;
    /**
     * A function that converts a stream into an array of bytes.
     * @internal
     */
    streamCollector?: __StreamCollector;
    /**
     * The function that will be used to convert a base64-encoded string to a byte array.
     * @internal
     */
    base64Decoder?: __Decoder;
    /**
     * The function that will be used to convert binary data to a base64-encoded string.
     * @internal
     */
    base64Encoder?: __Encoder;
    /**
     * The function that will be used to convert a UTF8-encoded string to a byte array.
     * @internal
     */
    utf8Decoder?: __Decoder;
    /**
     * The function that will be used to convert binary data to a UTF-8 encoded string.
     * @internal
     */
    utf8Encoder?: __Encoder;
    /**
     * The runtime environment.
     * @internal
     */
    runtime?: string;
    /**
     * Disable dynamically changing the endpoint of the client based on the hostPrefix
     * trait of an operation.
     */
    disableHostPrefix?: boolean;
    /**
     * Unique service identifier.
     * @internal
     */
    serviceId?: string;
    /**
     * Enables IPv6/IPv4 dualstack endpoint.
     */
    useDualstackEndpoint?: boolean | __Provider<boolean>;
    /**
     * Enables FIPS compatible endpoints.
     */
    useFipsEndpoint?: boolean | __Provider<boolean>;
    /**
     * The AWS region to which this client will send requests
     */
    region?: string | __Provider<string>;
    /**
     * Setting a client profile is similar to setting a value for the
     * AWS_PROFILE environment variable. Setting a profile on a client
     * in code only affects the single client instance, unlike AWS_PROFILE.
     *
     * When set, and only for environments where an AWS configuration
     * file exists, fields configurable by this file will be retrieved
     * from the specified profile within that file.
     * Conflicting code configuration and environment variables will
     * still have higher priority.
     *
     * For client credential resolution that involves checking the AWS
     * configuration file, the client's profile (this value) will be
     * used unless a different profile is set in the credential
     * provider options.
     *
     */
    profile?: string;
    /**
     * The provider populating default tracking information to be sent with `user-agent`, `x-amz-user-agent` header
     * @internal
     */
    defaultUserAgentProvider?: Provider<__UserAgent>;
    /**
     * Default credentials provider; Not available in browser runtime.
     * @deprecated
     * @internal
     */
    credentialDefaultProvider?: (input: any) => AwsCredentialIdentityProvider;
    /**
     * Value for how many times a request will be made at most in case of retry.
     */
    maxAttempts?: number | __Provider<number>;
    /**
     * Specifies which retry algorithm to use.
     * @see https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/Package/-smithy-util-retry/Enum/RETRY_MODES/
     *
     */
    retryMode?: string | __Provider<string>;
    /**
     * Optional logger for logging debug/info/warn/error.
     */
    logger?: __Logger;
    /**
     * Optional extensions
     */
    extensions?: RuntimeExtension[];
    /**
     * The {@link @smithy/smithy-client#DefaultsMode} that will be used to determine how certain default configuration options are resolved in the SDK.
     */
    defaultsMode?: __DefaultsMode | __Provider<__DefaultsMode>;
}
/**
 * @public
 */
export type SESClientConfigType = Partial<__SmithyConfiguration<__HttpHandlerOptions>> & ClientDefaults & UserAgentInputConfig & RetryInputConfig & RegionInputConfig & HostHeaderInputConfig & EndpointInputConfig<EndpointParameters> & HttpAuthSchemeInputConfig & ClientInputEndpointParameters;
/**
 * @public
 *
 *  The configuration interface of SESClient class constructor that set the region, credentials and other options.
 */
export interface SESClientConfig extends SESClientConfigType {
}
/**
 * @public
 */
export type SESClientResolvedConfigType = __SmithyResolvedConfiguration<__HttpHandlerOptions> & Required<ClientDefaults> & RuntimeExtensionsConfig & UserAgentResolvedConfig & RetryResolvedConfig & RegionResolvedConfig & HostHeaderResolvedConfig & EndpointResolvedConfig<EndpointParameters> & HttpAuthSchemeResolvedConfig & ClientResolvedEndpointParameters;
/**
 * @public
 *
 *  The resolved configuration interface of SESClient class. This is resolved and normalized from the {@link SESClientConfig | constructor configuration interface}.
 */
export interface SESClientResolvedConfig extends SESClientResolvedConfigType {
}
/**
 * <fullname>Amazon Simple Email Service</fullname>
 *          <p> This document contains reference information for the <a href="https://aws.amazon.com/ses/">Amazon Simple Email Service</a> (Amazon SES) API, version
 *             2010-12-01. This document is best used in conjunction with the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/Welcome.html">Amazon SES Developer
 *                 Guide</a>. </p>
 *          <note>
 *             <p> For a list of Amazon SES endpoints to use in service requests, see <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/regions.html">Regions and
 *                     Amazon SES</a> in the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/Welcome.html">Amazon SES Developer
 *                 Guide</a>.</p>
 *          </note>
 *          <p>This documentation contains reference information related to the following:</p>
 *          <ul>
 *             <li>
 *                <p>
 *                   <a href="https://docs.aws.amazon.com/ses/latest/APIReference/API_Operations.html">Amazon SES API Actions</a>
 *                </p>
 *             </li>
 *             <li>
 *                <p>
 *                   <a href="https://docs.aws.amazon.com/ses/latest/APIReference/API_Types.html">Amazon SES
 *                         API Data Types</a>
 *                </p>
 *             </li>
 *             <li>
 *                <p>
 *                   <a href="https://docs.aws.amazon.com/ses/latest/APIReference/CommonParameters.html">Common
 *                         Parameters</a>
 *                </p>
 *             </li>
 *             <li>
 *                <p>
 *                   <a href="https://docs.aws.amazon.com/ses/latest/APIReference/CommonErrors.html">Common Errors</a>
 *                </p>
 *             </li>
 *          </ul>
 * @public
 */
export declare class SESClient extends __Client<__HttpHandlerOptions, ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig> {
    /**
     * The resolved configuration of SESClient class. This is resolved and normalized from the {@link SESClientConfig | constructor configuration interface}.
     */
    readonly config: SESClientResolvedConfig;
    constructor(...[configuration]: __CheckOptionalClientConfig<SESClientConfig>);
    /**
     * Destroy underlying resources, like sockets. It's usually not necessary to do this.
     * However in Node.js, it's best to explicitly shut down the client's agent when it is no longer needed.
     * Otherwise, sockets might stay open for quite a long time before the server terminates them.
     */
    destroy(): void;
}
