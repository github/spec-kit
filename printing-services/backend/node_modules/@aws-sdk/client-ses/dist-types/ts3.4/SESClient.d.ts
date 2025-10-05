import {
  HostHeaderInputConfig,
  HostHeaderResolvedConfig,
} from "@aws-sdk/middleware-host-header";
import {
  UserAgentInputConfig,
  UserAgentResolvedConfig,
} from "@aws-sdk/middleware-user-agent";
import {
  RegionInputConfig,
  RegionResolvedConfig,
} from "@smithy/config-resolver";
import {
  EndpointInputConfig,
  EndpointResolvedConfig,
} from "@smithy/middleware-endpoint";
import {
  RetryInputConfig,
  RetryResolvedConfig,
} from "@smithy/middleware-retry";
import { HttpHandlerUserInput as __HttpHandlerUserInput } from "@smithy/protocol-http";
import {
  Client as __Client,
  DefaultsMode as __DefaultsMode,
  SmithyConfiguration as __SmithyConfiguration,
  SmithyResolvedConfiguration as __SmithyResolvedConfiguration,
} from "@smithy/smithy-client";
import {
  AwsCredentialIdentityProvider,
  BodyLengthCalculator as __BodyLengthCalculator,
  CheckOptionalClientConfig as __CheckOptionalClientConfig,
  ChecksumConstructor as __ChecksumConstructor,
  Decoder as __Decoder,
  Encoder as __Encoder,
  HashConstructor as __HashConstructor,
  HttpHandlerOptions as __HttpHandlerOptions,
  Logger as __Logger,
  Provider as __Provider,
  Provider,
  StreamCollector as __StreamCollector,
  UrlParser as __UrlParser,
  UserAgent as __UserAgent,
} from "@smithy/types";
import {
  HttpAuthSchemeInputConfig,
  HttpAuthSchemeResolvedConfig,
} from "./auth/httpAuthSchemeProvider";
import {
  CloneReceiptRuleSetCommandInput,
  CloneReceiptRuleSetCommandOutput,
} from "./commands/CloneReceiptRuleSetCommand";
import {
  CreateConfigurationSetCommandInput,
  CreateConfigurationSetCommandOutput,
} from "./commands/CreateConfigurationSetCommand";
import {
  CreateConfigurationSetEventDestinationCommandInput,
  CreateConfigurationSetEventDestinationCommandOutput,
} from "./commands/CreateConfigurationSetEventDestinationCommand";
import {
  CreateConfigurationSetTrackingOptionsCommandInput,
  CreateConfigurationSetTrackingOptionsCommandOutput,
} from "./commands/CreateConfigurationSetTrackingOptionsCommand";
import {
  CreateCustomVerificationEmailTemplateCommandInput,
  CreateCustomVerificationEmailTemplateCommandOutput,
} from "./commands/CreateCustomVerificationEmailTemplateCommand";
import {
  CreateReceiptFilterCommandInput,
  CreateReceiptFilterCommandOutput,
} from "./commands/CreateReceiptFilterCommand";
import {
  CreateReceiptRuleCommandInput,
  CreateReceiptRuleCommandOutput,
} from "./commands/CreateReceiptRuleCommand";
import {
  CreateReceiptRuleSetCommandInput,
  CreateReceiptRuleSetCommandOutput,
} from "./commands/CreateReceiptRuleSetCommand";
import {
  CreateTemplateCommandInput,
  CreateTemplateCommandOutput,
} from "./commands/CreateTemplateCommand";
import {
  DeleteConfigurationSetCommandInput,
  DeleteConfigurationSetCommandOutput,
} from "./commands/DeleteConfigurationSetCommand";
import {
  DeleteConfigurationSetEventDestinationCommandInput,
  DeleteConfigurationSetEventDestinationCommandOutput,
} from "./commands/DeleteConfigurationSetEventDestinationCommand";
import {
  DeleteConfigurationSetTrackingOptionsCommandInput,
  DeleteConfigurationSetTrackingOptionsCommandOutput,
} from "./commands/DeleteConfigurationSetTrackingOptionsCommand";
import {
  DeleteCustomVerificationEmailTemplateCommandInput,
  DeleteCustomVerificationEmailTemplateCommandOutput,
} from "./commands/DeleteCustomVerificationEmailTemplateCommand";
import {
  DeleteIdentityCommandInput,
  DeleteIdentityCommandOutput,
} from "./commands/DeleteIdentityCommand";
import {
  DeleteIdentityPolicyCommandInput,
  DeleteIdentityPolicyCommandOutput,
} from "./commands/DeleteIdentityPolicyCommand";
import {
  DeleteReceiptFilterCommandInput,
  DeleteReceiptFilterCommandOutput,
} from "./commands/DeleteReceiptFilterCommand";
import {
  DeleteReceiptRuleCommandInput,
  DeleteReceiptRuleCommandOutput,
} from "./commands/DeleteReceiptRuleCommand";
import {
  DeleteReceiptRuleSetCommandInput,
  DeleteReceiptRuleSetCommandOutput,
} from "./commands/DeleteReceiptRuleSetCommand";
import {
  DeleteTemplateCommandInput,
  DeleteTemplateCommandOutput,
} from "./commands/DeleteTemplateCommand";
import {
  DeleteVerifiedEmailAddressCommandInput,
  DeleteVerifiedEmailAddressCommandOutput,
} from "./commands/DeleteVerifiedEmailAddressCommand";
import {
  DescribeActiveReceiptRuleSetCommandInput,
  DescribeActiveReceiptRuleSetCommandOutput,
} from "./commands/DescribeActiveReceiptRuleSetCommand";
import {
  DescribeConfigurationSetCommandInput,
  DescribeConfigurationSetCommandOutput,
} from "./commands/DescribeConfigurationSetCommand";
import {
  DescribeReceiptRuleCommandInput,
  DescribeReceiptRuleCommandOutput,
} from "./commands/DescribeReceiptRuleCommand";
import {
  DescribeReceiptRuleSetCommandInput,
  DescribeReceiptRuleSetCommandOutput,
} from "./commands/DescribeReceiptRuleSetCommand";
import {
  GetAccountSendingEnabledCommandInput,
  GetAccountSendingEnabledCommandOutput,
} from "./commands/GetAccountSendingEnabledCommand";
import {
  GetCustomVerificationEmailTemplateCommandInput,
  GetCustomVerificationEmailTemplateCommandOutput,
} from "./commands/GetCustomVerificationEmailTemplateCommand";
import {
  GetIdentityDkimAttributesCommandInput,
  GetIdentityDkimAttributesCommandOutput,
} from "./commands/GetIdentityDkimAttributesCommand";
import {
  GetIdentityMailFromDomainAttributesCommandInput,
  GetIdentityMailFromDomainAttributesCommandOutput,
} from "./commands/GetIdentityMailFromDomainAttributesCommand";
import {
  GetIdentityNotificationAttributesCommandInput,
  GetIdentityNotificationAttributesCommandOutput,
} from "./commands/GetIdentityNotificationAttributesCommand";
import {
  GetIdentityPoliciesCommandInput,
  GetIdentityPoliciesCommandOutput,
} from "./commands/GetIdentityPoliciesCommand";
import {
  GetIdentityVerificationAttributesCommandInput,
  GetIdentityVerificationAttributesCommandOutput,
} from "./commands/GetIdentityVerificationAttributesCommand";
import {
  GetSendQuotaCommandInput,
  GetSendQuotaCommandOutput,
} from "./commands/GetSendQuotaCommand";
import {
  GetSendStatisticsCommandInput,
  GetSendStatisticsCommandOutput,
} from "./commands/GetSendStatisticsCommand";
import {
  GetTemplateCommandInput,
  GetTemplateCommandOutput,
} from "./commands/GetTemplateCommand";
import {
  ListConfigurationSetsCommandInput,
  ListConfigurationSetsCommandOutput,
} from "./commands/ListConfigurationSetsCommand";
import {
  ListCustomVerificationEmailTemplatesCommandInput,
  ListCustomVerificationEmailTemplatesCommandOutput,
} from "./commands/ListCustomVerificationEmailTemplatesCommand";
import {
  ListIdentitiesCommandInput,
  ListIdentitiesCommandOutput,
} from "./commands/ListIdentitiesCommand";
import {
  ListIdentityPoliciesCommandInput,
  ListIdentityPoliciesCommandOutput,
} from "./commands/ListIdentityPoliciesCommand";
import {
  ListReceiptFiltersCommandInput,
  ListReceiptFiltersCommandOutput,
} from "./commands/ListReceiptFiltersCommand";
import {
  ListReceiptRuleSetsCommandInput,
  ListReceiptRuleSetsCommandOutput,
} from "./commands/ListReceiptRuleSetsCommand";
import {
  ListTemplatesCommandInput,
  ListTemplatesCommandOutput,
} from "./commands/ListTemplatesCommand";
import {
  ListVerifiedEmailAddressesCommandInput,
  ListVerifiedEmailAddressesCommandOutput,
} from "./commands/ListVerifiedEmailAddressesCommand";
import {
  PutConfigurationSetDeliveryOptionsCommandInput,
  PutConfigurationSetDeliveryOptionsCommandOutput,
} from "./commands/PutConfigurationSetDeliveryOptionsCommand";
import {
  PutIdentityPolicyCommandInput,
  PutIdentityPolicyCommandOutput,
} from "./commands/PutIdentityPolicyCommand";
import {
  ReorderReceiptRuleSetCommandInput,
  ReorderReceiptRuleSetCommandOutput,
} from "./commands/ReorderReceiptRuleSetCommand";
import {
  SendBounceCommandInput,
  SendBounceCommandOutput,
} from "./commands/SendBounceCommand";
import {
  SendBulkTemplatedEmailCommandInput,
  SendBulkTemplatedEmailCommandOutput,
} from "./commands/SendBulkTemplatedEmailCommand";
import {
  SendCustomVerificationEmailCommandInput,
  SendCustomVerificationEmailCommandOutput,
} from "./commands/SendCustomVerificationEmailCommand";
import {
  SendEmailCommandInput,
  SendEmailCommandOutput,
} from "./commands/SendEmailCommand";
import {
  SendRawEmailCommandInput,
  SendRawEmailCommandOutput,
} from "./commands/SendRawEmailCommand";
import {
  SendTemplatedEmailCommandInput,
  SendTemplatedEmailCommandOutput,
} from "./commands/SendTemplatedEmailCommand";
import {
  SetActiveReceiptRuleSetCommandInput,
  SetActiveReceiptRuleSetCommandOutput,
} from "./commands/SetActiveReceiptRuleSetCommand";
import {
  SetIdentityDkimEnabledCommandInput,
  SetIdentityDkimEnabledCommandOutput,
} from "./commands/SetIdentityDkimEnabledCommand";
import {
  SetIdentityFeedbackForwardingEnabledCommandInput,
  SetIdentityFeedbackForwardingEnabledCommandOutput,
} from "./commands/SetIdentityFeedbackForwardingEnabledCommand";
import {
  SetIdentityHeadersInNotificationsEnabledCommandInput,
  SetIdentityHeadersInNotificationsEnabledCommandOutput,
} from "./commands/SetIdentityHeadersInNotificationsEnabledCommand";
import {
  SetIdentityMailFromDomainCommandInput,
  SetIdentityMailFromDomainCommandOutput,
} from "./commands/SetIdentityMailFromDomainCommand";
import {
  SetIdentityNotificationTopicCommandInput,
  SetIdentityNotificationTopicCommandOutput,
} from "./commands/SetIdentityNotificationTopicCommand";
import {
  SetReceiptRulePositionCommandInput,
  SetReceiptRulePositionCommandOutput,
} from "./commands/SetReceiptRulePositionCommand";
import {
  TestRenderTemplateCommandInput,
  TestRenderTemplateCommandOutput,
} from "./commands/TestRenderTemplateCommand";
import {
  UpdateAccountSendingEnabledCommandInput,
  UpdateAccountSendingEnabledCommandOutput,
} from "./commands/UpdateAccountSendingEnabledCommand";
import {
  UpdateConfigurationSetEventDestinationCommandInput,
  UpdateConfigurationSetEventDestinationCommandOutput,
} from "./commands/UpdateConfigurationSetEventDestinationCommand";
import {
  UpdateConfigurationSetReputationMetricsEnabledCommandInput,
  UpdateConfigurationSetReputationMetricsEnabledCommandOutput,
} from "./commands/UpdateConfigurationSetReputationMetricsEnabledCommand";
import {
  UpdateConfigurationSetSendingEnabledCommandInput,
  UpdateConfigurationSetSendingEnabledCommandOutput,
} from "./commands/UpdateConfigurationSetSendingEnabledCommand";
import {
  UpdateConfigurationSetTrackingOptionsCommandInput,
  UpdateConfigurationSetTrackingOptionsCommandOutput,
} from "./commands/UpdateConfigurationSetTrackingOptionsCommand";
import {
  UpdateCustomVerificationEmailTemplateCommandInput,
  UpdateCustomVerificationEmailTemplateCommandOutput,
} from "./commands/UpdateCustomVerificationEmailTemplateCommand";
import {
  UpdateReceiptRuleCommandInput,
  UpdateReceiptRuleCommandOutput,
} from "./commands/UpdateReceiptRuleCommand";
import {
  UpdateTemplateCommandInput,
  UpdateTemplateCommandOutput,
} from "./commands/UpdateTemplateCommand";
import {
  VerifyDomainDkimCommandInput,
  VerifyDomainDkimCommandOutput,
} from "./commands/VerifyDomainDkimCommand";
import {
  VerifyDomainIdentityCommandInput,
  VerifyDomainIdentityCommandOutput,
} from "./commands/VerifyDomainIdentityCommand";
import {
  VerifyEmailAddressCommandInput,
  VerifyEmailAddressCommandOutput,
} from "./commands/VerifyEmailAddressCommand";
import {
  VerifyEmailIdentityCommandInput,
  VerifyEmailIdentityCommandOutput,
} from "./commands/VerifyEmailIdentityCommand";
import {
  ClientInputEndpointParameters,
  ClientResolvedEndpointParameters,
  EndpointParameters,
} from "./endpoint/EndpointParameters";
import { RuntimeExtension, RuntimeExtensionsConfig } from "./runtimeExtensions";
export { __Client };
export type ServiceInputTypes =
  | CloneReceiptRuleSetCommandInput
  | CreateConfigurationSetCommandInput
  | CreateConfigurationSetEventDestinationCommandInput
  | CreateConfigurationSetTrackingOptionsCommandInput
  | CreateCustomVerificationEmailTemplateCommandInput
  | CreateReceiptFilterCommandInput
  | CreateReceiptRuleCommandInput
  | CreateReceiptRuleSetCommandInput
  | CreateTemplateCommandInput
  | DeleteConfigurationSetCommandInput
  | DeleteConfigurationSetEventDestinationCommandInput
  | DeleteConfigurationSetTrackingOptionsCommandInput
  | DeleteCustomVerificationEmailTemplateCommandInput
  | DeleteIdentityCommandInput
  | DeleteIdentityPolicyCommandInput
  | DeleteReceiptFilterCommandInput
  | DeleteReceiptRuleCommandInput
  | DeleteReceiptRuleSetCommandInput
  | DeleteTemplateCommandInput
  | DeleteVerifiedEmailAddressCommandInput
  | DescribeActiveReceiptRuleSetCommandInput
  | DescribeConfigurationSetCommandInput
  | DescribeReceiptRuleCommandInput
  | DescribeReceiptRuleSetCommandInput
  | GetAccountSendingEnabledCommandInput
  | GetCustomVerificationEmailTemplateCommandInput
  | GetIdentityDkimAttributesCommandInput
  | GetIdentityMailFromDomainAttributesCommandInput
  | GetIdentityNotificationAttributesCommandInput
  | GetIdentityPoliciesCommandInput
  | GetIdentityVerificationAttributesCommandInput
  | GetSendQuotaCommandInput
  | GetSendStatisticsCommandInput
  | GetTemplateCommandInput
  | ListConfigurationSetsCommandInput
  | ListCustomVerificationEmailTemplatesCommandInput
  | ListIdentitiesCommandInput
  | ListIdentityPoliciesCommandInput
  | ListReceiptFiltersCommandInput
  | ListReceiptRuleSetsCommandInput
  | ListTemplatesCommandInput
  | ListVerifiedEmailAddressesCommandInput
  | PutConfigurationSetDeliveryOptionsCommandInput
  | PutIdentityPolicyCommandInput
  | ReorderReceiptRuleSetCommandInput
  | SendBounceCommandInput
  | SendBulkTemplatedEmailCommandInput
  | SendCustomVerificationEmailCommandInput
  | SendEmailCommandInput
  | SendRawEmailCommandInput
  | SendTemplatedEmailCommandInput
  | SetActiveReceiptRuleSetCommandInput
  | SetIdentityDkimEnabledCommandInput
  | SetIdentityFeedbackForwardingEnabledCommandInput
  | SetIdentityHeadersInNotificationsEnabledCommandInput
  | SetIdentityMailFromDomainCommandInput
  | SetIdentityNotificationTopicCommandInput
  | SetReceiptRulePositionCommandInput
  | TestRenderTemplateCommandInput
  | UpdateAccountSendingEnabledCommandInput
  | UpdateConfigurationSetEventDestinationCommandInput
  | UpdateConfigurationSetReputationMetricsEnabledCommandInput
  | UpdateConfigurationSetSendingEnabledCommandInput
  | UpdateConfigurationSetTrackingOptionsCommandInput
  | UpdateCustomVerificationEmailTemplateCommandInput
  | UpdateReceiptRuleCommandInput
  | UpdateTemplateCommandInput
  | VerifyDomainDkimCommandInput
  | VerifyDomainIdentityCommandInput
  | VerifyEmailAddressCommandInput
  | VerifyEmailIdentityCommandInput;
export type ServiceOutputTypes =
  | CloneReceiptRuleSetCommandOutput
  | CreateConfigurationSetCommandOutput
  | CreateConfigurationSetEventDestinationCommandOutput
  | CreateConfigurationSetTrackingOptionsCommandOutput
  | CreateCustomVerificationEmailTemplateCommandOutput
  | CreateReceiptFilterCommandOutput
  | CreateReceiptRuleCommandOutput
  | CreateReceiptRuleSetCommandOutput
  | CreateTemplateCommandOutput
  | DeleteConfigurationSetCommandOutput
  | DeleteConfigurationSetEventDestinationCommandOutput
  | DeleteConfigurationSetTrackingOptionsCommandOutput
  | DeleteCustomVerificationEmailTemplateCommandOutput
  | DeleteIdentityCommandOutput
  | DeleteIdentityPolicyCommandOutput
  | DeleteReceiptFilterCommandOutput
  | DeleteReceiptRuleCommandOutput
  | DeleteReceiptRuleSetCommandOutput
  | DeleteTemplateCommandOutput
  | DeleteVerifiedEmailAddressCommandOutput
  | DescribeActiveReceiptRuleSetCommandOutput
  | DescribeConfigurationSetCommandOutput
  | DescribeReceiptRuleCommandOutput
  | DescribeReceiptRuleSetCommandOutput
  | GetAccountSendingEnabledCommandOutput
  | GetCustomVerificationEmailTemplateCommandOutput
  | GetIdentityDkimAttributesCommandOutput
  | GetIdentityMailFromDomainAttributesCommandOutput
  | GetIdentityNotificationAttributesCommandOutput
  | GetIdentityPoliciesCommandOutput
  | GetIdentityVerificationAttributesCommandOutput
  | GetSendQuotaCommandOutput
  | GetSendStatisticsCommandOutput
  | GetTemplateCommandOutput
  | ListConfigurationSetsCommandOutput
  | ListCustomVerificationEmailTemplatesCommandOutput
  | ListIdentitiesCommandOutput
  | ListIdentityPoliciesCommandOutput
  | ListReceiptFiltersCommandOutput
  | ListReceiptRuleSetsCommandOutput
  | ListTemplatesCommandOutput
  | ListVerifiedEmailAddressesCommandOutput
  | PutConfigurationSetDeliveryOptionsCommandOutput
  | PutIdentityPolicyCommandOutput
  | ReorderReceiptRuleSetCommandOutput
  | SendBounceCommandOutput
  | SendBulkTemplatedEmailCommandOutput
  | SendCustomVerificationEmailCommandOutput
  | SendEmailCommandOutput
  | SendRawEmailCommandOutput
  | SendTemplatedEmailCommandOutput
  | SetActiveReceiptRuleSetCommandOutput
  | SetIdentityDkimEnabledCommandOutput
  | SetIdentityFeedbackForwardingEnabledCommandOutput
  | SetIdentityHeadersInNotificationsEnabledCommandOutput
  | SetIdentityMailFromDomainCommandOutput
  | SetIdentityNotificationTopicCommandOutput
  | SetReceiptRulePositionCommandOutput
  | TestRenderTemplateCommandOutput
  | UpdateAccountSendingEnabledCommandOutput
  | UpdateConfigurationSetEventDestinationCommandOutput
  | UpdateConfigurationSetReputationMetricsEnabledCommandOutput
  | UpdateConfigurationSetSendingEnabledCommandOutput
  | UpdateConfigurationSetTrackingOptionsCommandOutput
  | UpdateCustomVerificationEmailTemplateCommandOutput
  | UpdateReceiptRuleCommandOutput
  | UpdateTemplateCommandOutput
  | VerifyDomainDkimCommandOutput
  | VerifyDomainIdentityCommandOutput
  | VerifyEmailAddressCommandOutput
  | VerifyEmailIdentityCommandOutput;
export interface ClientDefaults
  extends Partial<__SmithyConfiguration<__HttpHandlerOptions>> {
  requestHandler?: __HttpHandlerUserInput;
  sha256?: __ChecksumConstructor | __HashConstructor;
  urlParser?: __UrlParser;
  bodyLengthChecker?: __BodyLengthCalculator;
  streamCollector?: __StreamCollector;
  base64Decoder?: __Decoder;
  base64Encoder?: __Encoder;
  utf8Decoder?: __Decoder;
  utf8Encoder?: __Encoder;
  runtime?: string;
  disableHostPrefix?: boolean;
  serviceId?: string;
  useDualstackEndpoint?: boolean | __Provider<boolean>;
  useFipsEndpoint?: boolean | __Provider<boolean>;
  region?: string | __Provider<string>;
  profile?: string;
  defaultUserAgentProvider?: Provider<__UserAgent>;
  credentialDefaultProvider?: (input: any) => AwsCredentialIdentityProvider;
  maxAttempts?: number | __Provider<number>;
  retryMode?: string | __Provider<string>;
  logger?: __Logger;
  extensions?: RuntimeExtension[];
  defaultsMode?: __DefaultsMode | __Provider<__DefaultsMode>;
}
export type SESClientConfigType = Partial<
  __SmithyConfiguration<__HttpHandlerOptions>
> &
  ClientDefaults &
  UserAgentInputConfig &
  RetryInputConfig &
  RegionInputConfig &
  HostHeaderInputConfig &
  EndpointInputConfig<EndpointParameters> &
  HttpAuthSchemeInputConfig &
  ClientInputEndpointParameters;
export interface SESClientConfig extends SESClientConfigType {}
export type SESClientResolvedConfigType =
  __SmithyResolvedConfiguration<__HttpHandlerOptions> &
    Required<ClientDefaults> &
    RuntimeExtensionsConfig &
    UserAgentResolvedConfig &
    RetryResolvedConfig &
    RegionResolvedConfig &
    HostHeaderResolvedConfig &
    EndpointResolvedConfig<EndpointParameters> &
    HttpAuthSchemeResolvedConfig &
    ClientResolvedEndpointParameters;
export interface SESClientResolvedConfig extends SESClientResolvedConfigType {}
export declare class SESClient extends __Client<
  __HttpHandlerOptions,
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig
> {
  readonly config: SESClientResolvedConfig;
  constructor(...[configuration]: __CheckOptionalClientConfig<SESClientConfig>);
  destroy(): void;
}
