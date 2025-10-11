import { HttpHandlerOptions as __HttpHandlerOptions } from "@smithy/types";
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
import { SESClient } from "./SESClient";
export interface SES {
  cloneReceiptRuleSet(
    args: CloneReceiptRuleSetCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CloneReceiptRuleSetCommandOutput>;
  cloneReceiptRuleSet(
    args: CloneReceiptRuleSetCommandInput,
    cb: (err: any, data?: CloneReceiptRuleSetCommandOutput) => void
  ): void;
  cloneReceiptRuleSet(
    args: CloneReceiptRuleSetCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CloneReceiptRuleSetCommandOutput) => void
  ): void;
  createConfigurationSet(
    args: CreateConfigurationSetCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateConfigurationSetCommandOutput>;
  createConfigurationSet(
    args: CreateConfigurationSetCommandInput,
    cb: (err: any, data?: CreateConfigurationSetCommandOutput) => void
  ): void;
  createConfigurationSet(
    args: CreateConfigurationSetCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreateConfigurationSetCommandOutput) => void
  ): void;
  createConfigurationSetEventDestination(
    args: CreateConfigurationSetEventDestinationCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateConfigurationSetEventDestinationCommandOutput>;
  createConfigurationSetEventDestination(
    args: CreateConfigurationSetEventDestinationCommandInput,
    cb: (
      err: any,
      data?: CreateConfigurationSetEventDestinationCommandOutput
    ) => void
  ): void;
  createConfigurationSetEventDestination(
    args: CreateConfigurationSetEventDestinationCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: CreateConfigurationSetEventDestinationCommandOutput
    ) => void
  ): void;
  createConfigurationSetTrackingOptions(
    args: CreateConfigurationSetTrackingOptionsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateConfigurationSetTrackingOptionsCommandOutput>;
  createConfigurationSetTrackingOptions(
    args: CreateConfigurationSetTrackingOptionsCommandInput,
    cb: (
      err: any,
      data?: CreateConfigurationSetTrackingOptionsCommandOutput
    ) => void
  ): void;
  createConfigurationSetTrackingOptions(
    args: CreateConfigurationSetTrackingOptionsCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: CreateConfigurationSetTrackingOptionsCommandOutput
    ) => void
  ): void;
  createCustomVerificationEmailTemplate(
    args: CreateCustomVerificationEmailTemplateCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateCustomVerificationEmailTemplateCommandOutput>;
  createCustomVerificationEmailTemplate(
    args: CreateCustomVerificationEmailTemplateCommandInput,
    cb: (
      err: any,
      data?: CreateCustomVerificationEmailTemplateCommandOutput
    ) => void
  ): void;
  createCustomVerificationEmailTemplate(
    args: CreateCustomVerificationEmailTemplateCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: CreateCustomVerificationEmailTemplateCommandOutput
    ) => void
  ): void;
  createReceiptFilter(
    args: CreateReceiptFilterCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateReceiptFilterCommandOutput>;
  createReceiptFilter(
    args: CreateReceiptFilterCommandInput,
    cb: (err: any, data?: CreateReceiptFilterCommandOutput) => void
  ): void;
  createReceiptFilter(
    args: CreateReceiptFilterCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreateReceiptFilterCommandOutput) => void
  ): void;
  createReceiptRule(
    args: CreateReceiptRuleCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateReceiptRuleCommandOutput>;
  createReceiptRule(
    args: CreateReceiptRuleCommandInput,
    cb: (err: any, data?: CreateReceiptRuleCommandOutput) => void
  ): void;
  createReceiptRule(
    args: CreateReceiptRuleCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreateReceiptRuleCommandOutput) => void
  ): void;
  createReceiptRuleSet(
    args: CreateReceiptRuleSetCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateReceiptRuleSetCommandOutput>;
  createReceiptRuleSet(
    args: CreateReceiptRuleSetCommandInput,
    cb: (err: any, data?: CreateReceiptRuleSetCommandOutput) => void
  ): void;
  createReceiptRuleSet(
    args: CreateReceiptRuleSetCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreateReceiptRuleSetCommandOutput) => void
  ): void;
  createTemplate(
    args: CreateTemplateCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateTemplateCommandOutput>;
  createTemplate(
    args: CreateTemplateCommandInput,
    cb: (err: any, data?: CreateTemplateCommandOutput) => void
  ): void;
  createTemplate(
    args: CreateTemplateCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreateTemplateCommandOutput) => void
  ): void;
  deleteConfigurationSet(
    args: DeleteConfigurationSetCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteConfigurationSetCommandOutput>;
  deleteConfigurationSet(
    args: DeleteConfigurationSetCommandInput,
    cb: (err: any, data?: DeleteConfigurationSetCommandOutput) => void
  ): void;
  deleteConfigurationSet(
    args: DeleteConfigurationSetCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteConfigurationSetCommandOutput) => void
  ): void;
  deleteConfigurationSetEventDestination(
    args: DeleteConfigurationSetEventDestinationCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteConfigurationSetEventDestinationCommandOutput>;
  deleteConfigurationSetEventDestination(
    args: DeleteConfigurationSetEventDestinationCommandInput,
    cb: (
      err: any,
      data?: DeleteConfigurationSetEventDestinationCommandOutput
    ) => void
  ): void;
  deleteConfigurationSetEventDestination(
    args: DeleteConfigurationSetEventDestinationCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: DeleteConfigurationSetEventDestinationCommandOutput
    ) => void
  ): void;
  deleteConfigurationSetTrackingOptions(
    args: DeleteConfigurationSetTrackingOptionsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteConfigurationSetTrackingOptionsCommandOutput>;
  deleteConfigurationSetTrackingOptions(
    args: DeleteConfigurationSetTrackingOptionsCommandInput,
    cb: (
      err: any,
      data?: DeleteConfigurationSetTrackingOptionsCommandOutput
    ) => void
  ): void;
  deleteConfigurationSetTrackingOptions(
    args: DeleteConfigurationSetTrackingOptionsCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: DeleteConfigurationSetTrackingOptionsCommandOutput
    ) => void
  ): void;
  deleteCustomVerificationEmailTemplate(
    args: DeleteCustomVerificationEmailTemplateCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteCustomVerificationEmailTemplateCommandOutput>;
  deleteCustomVerificationEmailTemplate(
    args: DeleteCustomVerificationEmailTemplateCommandInput,
    cb: (
      err: any,
      data?: DeleteCustomVerificationEmailTemplateCommandOutput
    ) => void
  ): void;
  deleteCustomVerificationEmailTemplate(
    args: DeleteCustomVerificationEmailTemplateCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: DeleteCustomVerificationEmailTemplateCommandOutput
    ) => void
  ): void;
  deleteIdentity(
    args: DeleteIdentityCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteIdentityCommandOutput>;
  deleteIdentity(
    args: DeleteIdentityCommandInput,
    cb: (err: any, data?: DeleteIdentityCommandOutput) => void
  ): void;
  deleteIdentity(
    args: DeleteIdentityCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteIdentityCommandOutput) => void
  ): void;
  deleteIdentityPolicy(
    args: DeleteIdentityPolicyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteIdentityPolicyCommandOutput>;
  deleteIdentityPolicy(
    args: DeleteIdentityPolicyCommandInput,
    cb: (err: any, data?: DeleteIdentityPolicyCommandOutput) => void
  ): void;
  deleteIdentityPolicy(
    args: DeleteIdentityPolicyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteIdentityPolicyCommandOutput) => void
  ): void;
  deleteReceiptFilter(
    args: DeleteReceiptFilterCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteReceiptFilterCommandOutput>;
  deleteReceiptFilter(
    args: DeleteReceiptFilterCommandInput,
    cb: (err: any, data?: DeleteReceiptFilterCommandOutput) => void
  ): void;
  deleteReceiptFilter(
    args: DeleteReceiptFilterCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteReceiptFilterCommandOutput) => void
  ): void;
  deleteReceiptRule(
    args: DeleteReceiptRuleCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteReceiptRuleCommandOutput>;
  deleteReceiptRule(
    args: DeleteReceiptRuleCommandInput,
    cb: (err: any, data?: DeleteReceiptRuleCommandOutput) => void
  ): void;
  deleteReceiptRule(
    args: DeleteReceiptRuleCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteReceiptRuleCommandOutput) => void
  ): void;
  deleteReceiptRuleSet(
    args: DeleteReceiptRuleSetCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteReceiptRuleSetCommandOutput>;
  deleteReceiptRuleSet(
    args: DeleteReceiptRuleSetCommandInput,
    cb: (err: any, data?: DeleteReceiptRuleSetCommandOutput) => void
  ): void;
  deleteReceiptRuleSet(
    args: DeleteReceiptRuleSetCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteReceiptRuleSetCommandOutput) => void
  ): void;
  deleteTemplate(
    args: DeleteTemplateCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteTemplateCommandOutput>;
  deleteTemplate(
    args: DeleteTemplateCommandInput,
    cb: (err: any, data?: DeleteTemplateCommandOutput) => void
  ): void;
  deleteTemplate(
    args: DeleteTemplateCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteTemplateCommandOutput) => void
  ): void;
  deleteVerifiedEmailAddress(
    args: DeleteVerifiedEmailAddressCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteVerifiedEmailAddressCommandOutput>;
  deleteVerifiedEmailAddress(
    args: DeleteVerifiedEmailAddressCommandInput,
    cb: (err: any, data?: DeleteVerifiedEmailAddressCommandOutput) => void
  ): void;
  deleteVerifiedEmailAddress(
    args: DeleteVerifiedEmailAddressCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteVerifiedEmailAddressCommandOutput) => void
  ): void;
  describeActiveReceiptRuleSet(): Promise<DescribeActiveReceiptRuleSetCommandOutput>;
  describeActiveReceiptRuleSet(
    args: DescribeActiveReceiptRuleSetCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DescribeActiveReceiptRuleSetCommandOutput>;
  describeActiveReceiptRuleSet(
    args: DescribeActiveReceiptRuleSetCommandInput,
    cb: (err: any, data?: DescribeActiveReceiptRuleSetCommandOutput) => void
  ): void;
  describeActiveReceiptRuleSet(
    args: DescribeActiveReceiptRuleSetCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DescribeActiveReceiptRuleSetCommandOutput) => void
  ): void;
  describeConfigurationSet(
    args: DescribeConfigurationSetCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DescribeConfigurationSetCommandOutput>;
  describeConfigurationSet(
    args: DescribeConfigurationSetCommandInput,
    cb: (err: any, data?: DescribeConfigurationSetCommandOutput) => void
  ): void;
  describeConfigurationSet(
    args: DescribeConfigurationSetCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DescribeConfigurationSetCommandOutput) => void
  ): void;
  describeReceiptRule(
    args: DescribeReceiptRuleCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DescribeReceiptRuleCommandOutput>;
  describeReceiptRule(
    args: DescribeReceiptRuleCommandInput,
    cb: (err: any, data?: DescribeReceiptRuleCommandOutput) => void
  ): void;
  describeReceiptRule(
    args: DescribeReceiptRuleCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DescribeReceiptRuleCommandOutput) => void
  ): void;
  describeReceiptRuleSet(
    args: DescribeReceiptRuleSetCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DescribeReceiptRuleSetCommandOutput>;
  describeReceiptRuleSet(
    args: DescribeReceiptRuleSetCommandInput,
    cb: (err: any, data?: DescribeReceiptRuleSetCommandOutput) => void
  ): void;
  describeReceiptRuleSet(
    args: DescribeReceiptRuleSetCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DescribeReceiptRuleSetCommandOutput) => void
  ): void;
  getAccountSendingEnabled(): Promise<GetAccountSendingEnabledCommandOutput>;
  getAccountSendingEnabled(
    args: GetAccountSendingEnabledCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetAccountSendingEnabledCommandOutput>;
  getAccountSendingEnabled(
    args: GetAccountSendingEnabledCommandInput,
    cb: (err: any, data?: GetAccountSendingEnabledCommandOutput) => void
  ): void;
  getAccountSendingEnabled(
    args: GetAccountSendingEnabledCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetAccountSendingEnabledCommandOutput) => void
  ): void;
  getCustomVerificationEmailTemplate(
    args: GetCustomVerificationEmailTemplateCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetCustomVerificationEmailTemplateCommandOutput>;
  getCustomVerificationEmailTemplate(
    args: GetCustomVerificationEmailTemplateCommandInput,
    cb: (
      err: any,
      data?: GetCustomVerificationEmailTemplateCommandOutput
    ) => void
  ): void;
  getCustomVerificationEmailTemplate(
    args: GetCustomVerificationEmailTemplateCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: GetCustomVerificationEmailTemplateCommandOutput
    ) => void
  ): void;
  getIdentityDkimAttributes(
    args: GetIdentityDkimAttributesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetIdentityDkimAttributesCommandOutput>;
  getIdentityDkimAttributes(
    args: GetIdentityDkimAttributesCommandInput,
    cb: (err: any, data?: GetIdentityDkimAttributesCommandOutput) => void
  ): void;
  getIdentityDkimAttributes(
    args: GetIdentityDkimAttributesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetIdentityDkimAttributesCommandOutput) => void
  ): void;
  getIdentityMailFromDomainAttributes(
    args: GetIdentityMailFromDomainAttributesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetIdentityMailFromDomainAttributesCommandOutput>;
  getIdentityMailFromDomainAttributes(
    args: GetIdentityMailFromDomainAttributesCommandInput,
    cb: (
      err: any,
      data?: GetIdentityMailFromDomainAttributesCommandOutput
    ) => void
  ): void;
  getIdentityMailFromDomainAttributes(
    args: GetIdentityMailFromDomainAttributesCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: GetIdentityMailFromDomainAttributesCommandOutput
    ) => void
  ): void;
  getIdentityNotificationAttributes(
    args: GetIdentityNotificationAttributesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetIdentityNotificationAttributesCommandOutput>;
  getIdentityNotificationAttributes(
    args: GetIdentityNotificationAttributesCommandInput,
    cb: (
      err: any,
      data?: GetIdentityNotificationAttributesCommandOutput
    ) => void
  ): void;
  getIdentityNotificationAttributes(
    args: GetIdentityNotificationAttributesCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: GetIdentityNotificationAttributesCommandOutput
    ) => void
  ): void;
  getIdentityPolicies(
    args: GetIdentityPoliciesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetIdentityPoliciesCommandOutput>;
  getIdentityPolicies(
    args: GetIdentityPoliciesCommandInput,
    cb: (err: any, data?: GetIdentityPoliciesCommandOutput) => void
  ): void;
  getIdentityPolicies(
    args: GetIdentityPoliciesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetIdentityPoliciesCommandOutput) => void
  ): void;
  getIdentityVerificationAttributes(
    args: GetIdentityVerificationAttributesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetIdentityVerificationAttributesCommandOutput>;
  getIdentityVerificationAttributes(
    args: GetIdentityVerificationAttributesCommandInput,
    cb: (
      err: any,
      data?: GetIdentityVerificationAttributesCommandOutput
    ) => void
  ): void;
  getIdentityVerificationAttributes(
    args: GetIdentityVerificationAttributesCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: GetIdentityVerificationAttributesCommandOutput
    ) => void
  ): void;
  getSendQuota(): Promise<GetSendQuotaCommandOutput>;
  getSendQuota(
    args: GetSendQuotaCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetSendQuotaCommandOutput>;
  getSendQuota(
    args: GetSendQuotaCommandInput,
    cb: (err: any, data?: GetSendQuotaCommandOutput) => void
  ): void;
  getSendQuota(
    args: GetSendQuotaCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetSendQuotaCommandOutput) => void
  ): void;
  getSendStatistics(): Promise<GetSendStatisticsCommandOutput>;
  getSendStatistics(
    args: GetSendStatisticsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetSendStatisticsCommandOutput>;
  getSendStatistics(
    args: GetSendStatisticsCommandInput,
    cb: (err: any, data?: GetSendStatisticsCommandOutput) => void
  ): void;
  getSendStatistics(
    args: GetSendStatisticsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetSendStatisticsCommandOutput) => void
  ): void;
  getTemplate(
    args: GetTemplateCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetTemplateCommandOutput>;
  getTemplate(
    args: GetTemplateCommandInput,
    cb: (err: any, data?: GetTemplateCommandOutput) => void
  ): void;
  getTemplate(
    args: GetTemplateCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetTemplateCommandOutput) => void
  ): void;
  listConfigurationSets(): Promise<ListConfigurationSetsCommandOutput>;
  listConfigurationSets(
    args: ListConfigurationSetsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListConfigurationSetsCommandOutput>;
  listConfigurationSets(
    args: ListConfigurationSetsCommandInput,
    cb: (err: any, data?: ListConfigurationSetsCommandOutput) => void
  ): void;
  listConfigurationSets(
    args: ListConfigurationSetsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListConfigurationSetsCommandOutput) => void
  ): void;
  listCustomVerificationEmailTemplates(): Promise<ListCustomVerificationEmailTemplatesCommandOutput>;
  listCustomVerificationEmailTemplates(
    args: ListCustomVerificationEmailTemplatesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListCustomVerificationEmailTemplatesCommandOutput>;
  listCustomVerificationEmailTemplates(
    args: ListCustomVerificationEmailTemplatesCommandInput,
    cb: (
      err: any,
      data?: ListCustomVerificationEmailTemplatesCommandOutput
    ) => void
  ): void;
  listCustomVerificationEmailTemplates(
    args: ListCustomVerificationEmailTemplatesCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: ListCustomVerificationEmailTemplatesCommandOutput
    ) => void
  ): void;
  listIdentities(): Promise<ListIdentitiesCommandOutput>;
  listIdentities(
    args: ListIdentitiesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListIdentitiesCommandOutput>;
  listIdentities(
    args: ListIdentitiesCommandInput,
    cb: (err: any, data?: ListIdentitiesCommandOutput) => void
  ): void;
  listIdentities(
    args: ListIdentitiesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListIdentitiesCommandOutput) => void
  ): void;
  listIdentityPolicies(
    args: ListIdentityPoliciesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListIdentityPoliciesCommandOutput>;
  listIdentityPolicies(
    args: ListIdentityPoliciesCommandInput,
    cb: (err: any, data?: ListIdentityPoliciesCommandOutput) => void
  ): void;
  listIdentityPolicies(
    args: ListIdentityPoliciesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListIdentityPoliciesCommandOutput) => void
  ): void;
  listReceiptFilters(): Promise<ListReceiptFiltersCommandOutput>;
  listReceiptFilters(
    args: ListReceiptFiltersCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListReceiptFiltersCommandOutput>;
  listReceiptFilters(
    args: ListReceiptFiltersCommandInput,
    cb: (err: any, data?: ListReceiptFiltersCommandOutput) => void
  ): void;
  listReceiptFilters(
    args: ListReceiptFiltersCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListReceiptFiltersCommandOutput) => void
  ): void;
  listReceiptRuleSets(): Promise<ListReceiptRuleSetsCommandOutput>;
  listReceiptRuleSets(
    args: ListReceiptRuleSetsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListReceiptRuleSetsCommandOutput>;
  listReceiptRuleSets(
    args: ListReceiptRuleSetsCommandInput,
    cb: (err: any, data?: ListReceiptRuleSetsCommandOutput) => void
  ): void;
  listReceiptRuleSets(
    args: ListReceiptRuleSetsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListReceiptRuleSetsCommandOutput) => void
  ): void;
  listTemplates(): Promise<ListTemplatesCommandOutput>;
  listTemplates(
    args: ListTemplatesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListTemplatesCommandOutput>;
  listTemplates(
    args: ListTemplatesCommandInput,
    cb: (err: any, data?: ListTemplatesCommandOutput) => void
  ): void;
  listTemplates(
    args: ListTemplatesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListTemplatesCommandOutput) => void
  ): void;
  listVerifiedEmailAddresses(): Promise<ListVerifiedEmailAddressesCommandOutput>;
  listVerifiedEmailAddresses(
    args: ListVerifiedEmailAddressesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListVerifiedEmailAddressesCommandOutput>;
  listVerifiedEmailAddresses(
    args: ListVerifiedEmailAddressesCommandInput,
    cb: (err: any, data?: ListVerifiedEmailAddressesCommandOutput) => void
  ): void;
  listVerifiedEmailAddresses(
    args: ListVerifiedEmailAddressesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListVerifiedEmailAddressesCommandOutput) => void
  ): void;
  putConfigurationSetDeliveryOptions(
    args: PutConfigurationSetDeliveryOptionsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<PutConfigurationSetDeliveryOptionsCommandOutput>;
  putConfigurationSetDeliveryOptions(
    args: PutConfigurationSetDeliveryOptionsCommandInput,
    cb: (
      err: any,
      data?: PutConfigurationSetDeliveryOptionsCommandOutput
    ) => void
  ): void;
  putConfigurationSetDeliveryOptions(
    args: PutConfigurationSetDeliveryOptionsCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: PutConfigurationSetDeliveryOptionsCommandOutput
    ) => void
  ): void;
  putIdentityPolicy(
    args: PutIdentityPolicyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<PutIdentityPolicyCommandOutput>;
  putIdentityPolicy(
    args: PutIdentityPolicyCommandInput,
    cb: (err: any, data?: PutIdentityPolicyCommandOutput) => void
  ): void;
  putIdentityPolicy(
    args: PutIdentityPolicyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: PutIdentityPolicyCommandOutput) => void
  ): void;
  reorderReceiptRuleSet(
    args: ReorderReceiptRuleSetCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ReorderReceiptRuleSetCommandOutput>;
  reorderReceiptRuleSet(
    args: ReorderReceiptRuleSetCommandInput,
    cb: (err: any, data?: ReorderReceiptRuleSetCommandOutput) => void
  ): void;
  reorderReceiptRuleSet(
    args: ReorderReceiptRuleSetCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ReorderReceiptRuleSetCommandOutput) => void
  ): void;
  sendBounce(
    args: SendBounceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SendBounceCommandOutput>;
  sendBounce(
    args: SendBounceCommandInput,
    cb: (err: any, data?: SendBounceCommandOutput) => void
  ): void;
  sendBounce(
    args: SendBounceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SendBounceCommandOutput) => void
  ): void;
  sendBulkTemplatedEmail(
    args: SendBulkTemplatedEmailCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SendBulkTemplatedEmailCommandOutput>;
  sendBulkTemplatedEmail(
    args: SendBulkTemplatedEmailCommandInput,
    cb: (err: any, data?: SendBulkTemplatedEmailCommandOutput) => void
  ): void;
  sendBulkTemplatedEmail(
    args: SendBulkTemplatedEmailCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SendBulkTemplatedEmailCommandOutput) => void
  ): void;
  sendCustomVerificationEmail(
    args: SendCustomVerificationEmailCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SendCustomVerificationEmailCommandOutput>;
  sendCustomVerificationEmail(
    args: SendCustomVerificationEmailCommandInput,
    cb: (err: any, data?: SendCustomVerificationEmailCommandOutput) => void
  ): void;
  sendCustomVerificationEmail(
    args: SendCustomVerificationEmailCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SendCustomVerificationEmailCommandOutput) => void
  ): void;
  sendEmail(
    args: SendEmailCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SendEmailCommandOutput>;
  sendEmail(
    args: SendEmailCommandInput,
    cb: (err: any, data?: SendEmailCommandOutput) => void
  ): void;
  sendEmail(
    args: SendEmailCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SendEmailCommandOutput) => void
  ): void;
  sendRawEmail(
    args: SendRawEmailCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SendRawEmailCommandOutput>;
  sendRawEmail(
    args: SendRawEmailCommandInput,
    cb: (err: any, data?: SendRawEmailCommandOutput) => void
  ): void;
  sendRawEmail(
    args: SendRawEmailCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SendRawEmailCommandOutput) => void
  ): void;
  sendTemplatedEmail(
    args: SendTemplatedEmailCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SendTemplatedEmailCommandOutput>;
  sendTemplatedEmail(
    args: SendTemplatedEmailCommandInput,
    cb: (err: any, data?: SendTemplatedEmailCommandOutput) => void
  ): void;
  sendTemplatedEmail(
    args: SendTemplatedEmailCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SendTemplatedEmailCommandOutput) => void
  ): void;
  setActiveReceiptRuleSet(): Promise<SetActiveReceiptRuleSetCommandOutput>;
  setActiveReceiptRuleSet(
    args: SetActiveReceiptRuleSetCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SetActiveReceiptRuleSetCommandOutput>;
  setActiveReceiptRuleSet(
    args: SetActiveReceiptRuleSetCommandInput,
    cb: (err: any, data?: SetActiveReceiptRuleSetCommandOutput) => void
  ): void;
  setActiveReceiptRuleSet(
    args: SetActiveReceiptRuleSetCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SetActiveReceiptRuleSetCommandOutput) => void
  ): void;
  setIdentityDkimEnabled(
    args: SetIdentityDkimEnabledCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SetIdentityDkimEnabledCommandOutput>;
  setIdentityDkimEnabled(
    args: SetIdentityDkimEnabledCommandInput,
    cb: (err: any, data?: SetIdentityDkimEnabledCommandOutput) => void
  ): void;
  setIdentityDkimEnabled(
    args: SetIdentityDkimEnabledCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SetIdentityDkimEnabledCommandOutput) => void
  ): void;
  setIdentityFeedbackForwardingEnabled(
    args: SetIdentityFeedbackForwardingEnabledCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SetIdentityFeedbackForwardingEnabledCommandOutput>;
  setIdentityFeedbackForwardingEnabled(
    args: SetIdentityFeedbackForwardingEnabledCommandInput,
    cb: (
      err: any,
      data?: SetIdentityFeedbackForwardingEnabledCommandOutput
    ) => void
  ): void;
  setIdentityFeedbackForwardingEnabled(
    args: SetIdentityFeedbackForwardingEnabledCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: SetIdentityFeedbackForwardingEnabledCommandOutput
    ) => void
  ): void;
  setIdentityHeadersInNotificationsEnabled(
    args: SetIdentityHeadersInNotificationsEnabledCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SetIdentityHeadersInNotificationsEnabledCommandOutput>;
  setIdentityHeadersInNotificationsEnabled(
    args: SetIdentityHeadersInNotificationsEnabledCommandInput,
    cb: (
      err: any,
      data?: SetIdentityHeadersInNotificationsEnabledCommandOutput
    ) => void
  ): void;
  setIdentityHeadersInNotificationsEnabled(
    args: SetIdentityHeadersInNotificationsEnabledCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: SetIdentityHeadersInNotificationsEnabledCommandOutput
    ) => void
  ): void;
  setIdentityMailFromDomain(
    args: SetIdentityMailFromDomainCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SetIdentityMailFromDomainCommandOutput>;
  setIdentityMailFromDomain(
    args: SetIdentityMailFromDomainCommandInput,
    cb: (err: any, data?: SetIdentityMailFromDomainCommandOutput) => void
  ): void;
  setIdentityMailFromDomain(
    args: SetIdentityMailFromDomainCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SetIdentityMailFromDomainCommandOutput) => void
  ): void;
  setIdentityNotificationTopic(
    args: SetIdentityNotificationTopicCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SetIdentityNotificationTopicCommandOutput>;
  setIdentityNotificationTopic(
    args: SetIdentityNotificationTopicCommandInput,
    cb: (err: any, data?: SetIdentityNotificationTopicCommandOutput) => void
  ): void;
  setIdentityNotificationTopic(
    args: SetIdentityNotificationTopicCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SetIdentityNotificationTopicCommandOutput) => void
  ): void;
  setReceiptRulePosition(
    args: SetReceiptRulePositionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SetReceiptRulePositionCommandOutput>;
  setReceiptRulePosition(
    args: SetReceiptRulePositionCommandInput,
    cb: (err: any, data?: SetReceiptRulePositionCommandOutput) => void
  ): void;
  setReceiptRulePosition(
    args: SetReceiptRulePositionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SetReceiptRulePositionCommandOutput) => void
  ): void;
  testRenderTemplate(
    args: TestRenderTemplateCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<TestRenderTemplateCommandOutput>;
  testRenderTemplate(
    args: TestRenderTemplateCommandInput,
    cb: (err: any, data?: TestRenderTemplateCommandOutput) => void
  ): void;
  testRenderTemplate(
    args: TestRenderTemplateCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: TestRenderTemplateCommandOutput) => void
  ): void;
  updateAccountSendingEnabled(): Promise<UpdateAccountSendingEnabledCommandOutput>;
  updateAccountSendingEnabled(
    args: UpdateAccountSendingEnabledCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateAccountSendingEnabledCommandOutput>;
  updateAccountSendingEnabled(
    args: UpdateAccountSendingEnabledCommandInput,
    cb: (err: any, data?: UpdateAccountSendingEnabledCommandOutput) => void
  ): void;
  updateAccountSendingEnabled(
    args: UpdateAccountSendingEnabledCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateAccountSendingEnabledCommandOutput) => void
  ): void;
  updateConfigurationSetEventDestination(
    args: UpdateConfigurationSetEventDestinationCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateConfigurationSetEventDestinationCommandOutput>;
  updateConfigurationSetEventDestination(
    args: UpdateConfigurationSetEventDestinationCommandInput,
    cb: (
      err: any,
      data?: UpdateConfigurationSetEventDestinationCommandOutput
    ) => void
  ): void;
  updateConfigurationSetEventDestination(
    args: UpdateConfigurationSetEventDestinationCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: UpdateConfigurationSetEventDestinationCommandOutput
    ) => void
  ): void;
  updateConfigurationSetReputationMetricsEnabled(
    args: UpdateConfigurationSetReputationMetricsEnabledCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateConfigurationSetReputationMetricsEnabledCommandOutput>;
  updateConfigurationSetReputationMetricsEnabled(
    args: UpdateConfigurationSetReputationMetricsEnabledCommandInput,
    cb: (
      err: any,
      data?: UpdateConfigurationSetReputationMetricsEnabledCommandOutput
    ) => void
  ): void;
  updateConfigurationSetReputationMetricsEnabled(
    args: UpdateConfigurationSetReputationMetricsEnabledCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: UpdateConfigurationSetReputationMetricsEnabledCommandOutput
    ) => void
  ): void;
  updateConfigurationSetSendingEnabled(
    args: UpdateConfigurationSetSendingEnabledCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateConfigurationSetSendingEnabledCommandOutput>;
  updateConfigurationSetSendingEnabled(
    args: UpdateConfigurationSetSendingEnabledCommandInput,
    cb: (
      err: any,
      data?: UpdateConfigurationSetSendingEnabledCommandOutput
    ) => void
  ): void;
  updateConfigurationSetSendingEnabled(
    args: UpdateConfigurationSetSendingEnabledCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: UpdateConfigurationSetSendingEnabledCommandOutput
    ) => void
  ): void;
  updateConfigurationSetTrackingOptions(
    args: UpdateConfigurationSetTrackingOptionsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateConfigurationSetTrackingOptionsCommandOutput>;
  updateConfigurationSetTrackingOptions(
    args: UpdateConfigurationSetTrackingOptionsCommandInput,
    cb: (
      err: any,
      data?: UpdateConfigurationSetTrackingOptionsCommandOutput
    ) => void
  ): void;
  updateConfigurationSetTrackingOptions(
    args: UpdateConfigurationSetTrackingOptionsCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: UpdateConfigurationSetTrackingOptionsCommandOutput
    ) => void
  ): void;
  updateCustomVerificationEmailTemplate(
    args: UpdateCustomVerificationEmailTemplateCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateCustomVerificationEmailTemplateCommandOutput>;
  updateCustomVerificationEmailTemplate(
    args: UpdateCustomVerificationEmailTemplateCommandInput,
    cb: (
      err: any,
      data?: UpdateCustomVerificationEmailTemplateCommandOutput
    ) => void
  ): void;
  updateCustomVerificationEmailTemplate(
    args: UpdateCustomVerificationEmailTemplateCommandInput,
    options: __HttpHandlerOptions,
    cb: (
      err: any,
      data?: UpdateCustomVerificationEmailTemplateCommandOutput
    ) => void
  ): void;
  updateReceiptRule(
    args: UpdateReceiptRuleCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateReceiptRuleCommandOutput>;
  updateReceiptRule(
    args: UpdateReceiptRuleCommandInput,
    cb: (err: any, data?: UpdateReceiptRuleCommandOutput) => void
  ): void;
  updateReceiptRule(
    args: UpdateReceiptRuleCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateReceiptRuleCommandOutput) => void
  ): void;
  updateTemplate(
    args: UpdateTemplateCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateTemplateCommandOutput>;
  updateTemplate(
    args: UpdateTemplateCommandInput,
    cb: (err: any, data?: UpdateTemplateCommandOutput) => void
  ): void;
  updateTemplate(
    args: UpdateTemplateCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateTemplateCommandOutput) => void
  ): void;
  verifyDomainDkim(
    args: VerifyDomainDkimCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<VerifyDomainDkimCommandOutput>;
  verifyDomainDkim(
    args: VerifyDomainDkimCommandInput,
    cb: (err: any, data?: VerifyDomainDkimCommandOutput) => void
  ): void;
  verifyDomainDkim(
    args: VerifyDomainDkimCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: VerifyDomainDkimCommandOutput) => void
  ): void;
  verifyDomainIdentity(
    args: VerifyDomainIdentityCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<VerifyDomainIdentityCommandOutput>;
  verifyDomainIdentity(
    args: VerifyDomainIdentityCommandInput,
    cb: (err: any, data?: VerifyDomainIdentityCommandOutput) => void
  ): void;
  verifyDomainIdentity(
    args: VerifyDomainIdentityCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: VerifyDomainIdentityCommandOutput) => void
  ): void;
  verifyEmailAddress(
    args: VerifyEmailAddressCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<VerifyEmailAddressCommandOutput>;
  verifyEmailAddress(
    args: VerifyEmailAddressCommandInput,
    cb: (err: any, data?: VerifyEmailAddressCommandOutput) => void
  ): void;
  verifyEmailAddress(
    args: VerifyEmailAddressCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: VerifyEmailAddressCommandOutput) => void
  ): void;
  verifyEmailIdentity(
    args: VerifyEmailIdentityCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<VerifyEmailIdentityCommandOutput>;
  verifyEmailIdentity(
    args: VerifyEmailIdentityCommandInput,
    cb: (err: any, data?: VerifyEmailIdentityCommandOutput) => void
  ): void;
  verifyEmailIdentity(
    args: VerifyEmailIdentityCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: VerifyEmailIdentityCommandOutput) => void
  ): void;
}
export declare class SES extends SESClient implements SES {}
