import {
  HttpRequest as __HttpRequest,
  HttpResponse as __HttpResponse,
} from "@smithy/protocol-http";
import { SerdeContext as __SerdeContext } from "@smithy/types";
import {
  CloneReceiptRuleSetCommandInput,
  CloneReceiptRuleSetCommandOutput,
} from "../commands/CloneReceiptRuleSetCommand";
import {
  CreateConfigurationSetCommandInput,
  CreateConfigurationSetCommandOutput,
} from "../commands/CreateConfigurationSetCommand";
import {
  CreateConfigurationSetEventDestinationCommandInput,
  CreateConfigurationSetEventDestinationCommandOutput,
} from "../commands/CreateConfigurationSetEventDestinationCommand";
import {
  CreateConfigurationSetTrackingOptionsCommandInput,
  CreateConfigurationSetTrackingOptionsCommandOutput,
} from "../commands/CreateConfigurationSetTrackingOptionsCommand";
import {
  CreateCustomVerificationEmailTemplateCommandInput,
  CreateCustomVerificationEmailTemplateCommandOutput,
} from "../commands/CreateCustomVerificationEmailTemplateCommand";
import {
  CreateReceiptFilterCommandInput,
  CreateReceiptFilterCommandOutput,
} from "../commands/CreateReceiptFilterCommand";
import {
  CreateReceiptRuleCommandInput,
  CreateReceiptRuleCommandOutput,
} from "../commands/CreateReceiptRuleCommand";
import {
  CreateReceiptRuleSetCommandInput,
  CreateReceiptRuleSetCommandOutput,
} from "../commands/CreateReceiptRuleSetCommand";
import {
  CreateTemplateCommandInput,
  CreateTemplateCommandOutput,
} from "../commands/CreateTemplateCommand";
import {
  DeleteConfigurationSetCommandInput,
  DeleteConfigurationSetCommandOutput,
} from "../commands/DeleteConfigurationSetCommand";
import {
  DeleteConfigurationSetEventDestinationCommandInput,
  DeleteConfigurationSetEventDestinationCommandOutput,
} from "../commands/DeleteConfigurationSetEventDestinationCommand";
import {
  DeleteConfigurationSetTrackingOptionsCommandInput,
  DeleteConfigurationSetTrackingOptionsCommandOutput,
} from "../commands/DeleteConfigurationSetTrackingOptionsCommand";
import {
  DeleteCustomVerificationEmailTemplateCommandInput,
  DeleteCustomVerificationEmailTemplateCommandOutput,
} from "../commands/DeleteCustomVerificationEmailTemplateCommand";
import {
  DeleteIdentityCommandInput,
  DeleteIdentityCommandOutput,
} from "../commands/DeleteIdentityCommand";
import {
  DeleteIdentityPolicyCommandInput,
  DeleteIdentityPolicyCommandOutput,
} from "../commands/DeleteIdentityPolicyCommand";
import {
  DeleteReceiptFilterCommandInput,
  DeleteReceiptFilterCommandOutput,
} from "../commands/DeleteReceiptFilterCommand";
import {
  DeleteReceiptRuleCommandInput,
  DeleteReceiptRuleCommandOutput,
} from "../commands/DeleteReceiptRuleCommand";
import {
  DeleteReceiptRuleSetCommandInput,
  DeleteReceiptRuleSetCommandOutput,
} from "../commands/DeleteReceiptRuleSetCommand";
import {
  DeleteTemplateCommandInput,
  DeleteTemplateCommandOutput,
} from "../commands/DeleteTemplateCommand";
import {
  DeleteVerifiedEmailAddressCommandInput,
  DeleteVerifiedEmailAddressCommandOutput,
} from "../commands/DeleteVerifiedEmailAddressCommand";
import {
  DescribeActiveReceiptRuleSetCommandInput,
  DescribeActiveReceiptRuleSetCommandOutput,
} from "../commands/DescribeActiveReceiptRuleSetCommand";
import {
  DescribeConfigurationSetCommandInput,
  DescribeConfigurationSetCommandOutput,
} from "../commands/DescribeConfigurationSetCommand";
import {
  DescribeReceiptRuleCommandInput,
  DescribeReceiptRuleCommandOutput,
} from "../commands/DescribeReceiptRuleCommand";
import {
  DescribeReceiptRuleSetCommandInput,
  DescribeReceiptRuleSetCommandOutput,
} from "../commands/DescribeReceiptRuleSetCommand";
import {
  GetAccountSendingEnabledCommandInput,
  GetAccountSendingEnabledCommandOutput,
} from "../commands/GetAccountSendingEnabledCommand";
import {
  GetCustomVerificationEmailTemplateCommandInput,
  GetCustomVerificationEmailTemplateCommandOutput,
} from "../commands/GetCustomVerificationEmailTemplateCommand";
import {
  GetIdentityDkimAttributesCommandInput,
  GetIdentityDkimAttributesCommandOutput,
} from "../commands/GetIdentityDkimAttributesCommand";
import {
  GetIdentityMailFromDomainAttributesCommandInput,
  GetIdentityMailFromDomainAttributesCommandOutput,
} from "../commands/GetIdentityMailFromDomainAttributesCommand";
import {
  GetIdentityNotificationAttributesCommandInput,
  GetIdentityNotificationAttributesCommandOutput,
} from "../commands/GetIdentityNotificationAttributesCommand";
import {
  GetIdentityPoliciesCommandInput,
  GetIdentityPoliciesCommandOutput,
} from "../commands/GetIdentityPoliciesCommand";
import {
  GetIdentityVerificationAttributesCommandInput,
  GetIdentityVerificationAttributesCommandOutput,
} from "../commands/GetIdentityVerificationAttributesCommand";
import {
  GetSendQuotaCommandInput,
  GetSendQuotaCommandOutput,
} from "../commands/GetSendQuotaCommand";
import {
  GetSendStatisticsCommandInput,
  GetSendStatisticsCommandOutput,
} from "../commands/GetSendStatisticsCommand";
import {
  GetTemplateCommandInput,
  GetTemplateCommandOutput,
} from "../commands/GetTemplateCommand";
import {
  ListConfigurationSetsCommandInput,
  ListConfigurationSetsCommandOutput,
} from "../commands/ListConfigurationSetsCommand";
import {
  ListCustomVerificationEmailTemplatesCommandInput,
  ListCustomVerificationEmailTemplatesCommandOutput,
} from "../commands/ListCustomVerificationEmailTemplatesCommand";
import {
  ListIdentitiesCommandInput,
  ListIdentitiesCommandOutput,
} from "../commands/ListIdentitiesCommand";
import {
  ListIdentityPoliciesCommandInput,
  ListIdentityPoliciesCommandOutput,
} from "../commands/ListIdentityPoliciesCommand";
import {
  ListReceiptFiltersCommandInput,
  ListReceiptFiltersCommandOutput,
} from "../commands/ListReceiptFiltersCommand";
import {
  ListReceiptRuleSetsCommandInput,
  ListReceiptRuleSetsCommandOutput,
} from "../commands/ListReceiptRuleSetsCommand";
import {
  ListTemplatesCommandInput,
  ListTemplatesCommandOutput,
} from "../commands/ListTemplatesCommand";
import {
  ListVerifiedEmailAddressesCommandInput,
  ListVerifiedEmailAddressesCommandOutput,
} from "../commands/ListVerifiedEmailAddressesCommand";
import {
  PutConfigurationSetDeliveryOptionsCommandInput,
  PutConfigurationSetDeliveryOptionsCommandOutput,
} from "../commands/PutConfigurationSetDeliveryOptionsCommand";
import {
  PutIdentityPolicyCommandInput,
  PutIdentityPolicyCommandOutput,
} from "../commands/PutIdentityPolicyCommand";
import {
  ReorderReceiptRuleSetCommandInput,
  ReorderReceiptRuleSetCommandOutput,
} from "../commands/ReorderReceiptRuleSetCommand";
import {
  SendBounceCommandInput,
  SendBounceCommandOutput,
} from "../commands/SendBounceCommand";
import {
  SendBulkTemplatedEmailCommandInput,
  SendBulkTemplatedEmailCommandOutput,
} from "../commands/SendBulkTemplatedEmailCommand";
import {
  SendCustomVerificationEmailCommandInput,
  SendCustomVerificationEmailCommandOutput,
} from "../commands/SendCustomVerificationEmailCommand";
import {
  SendEmailCommandInput,
  SendEmailCommandOutput,
} from "../commands/SendEmailCommand";
import {
  SendRawEmailCommandInput,
  SendRawEmailCommandOutput,
} from "../commands/SendRawEmailCommand";
import {
  SendTemplatedEmailCommandInput,
  SendTemplatedEmailCommandOutput,
} from "../commands/SendTemplatedEmailCommand";
import {
  SetActiveReceiptRuleSetCommandInput,
  SetActiveReceiptRuleSetCommandOutput,
} from "../commands/SetActiveReceiptRuleSetCommand";
import {
  SetIdentityDkimEnabledCommandInput,
  SetIdentityDkimEnabledCommandOutput,
} from "../commands/SetIdentityDkimEnabledCommand";
import {
  SetIdentityFeedbackForwardingEnabledCommandInput,
  SetIdentityFeedbackForwardingEnabledCommandOutput,
} from "../commands/SetIdentityFeedbackForwardingEnabledCommand";
import {
  SetIdentityHeadersInNotificationsEnabledCommandInput,
  SetIdentityHeadersInNotificationsEnabledCommandOutput,
} from "../commands/SetIdentityHeadersInNotificationsEnabledCommand";
import {
  SetIdentityMailFromDomainCommandInput,
  SetIdentityMailFromDomainCommandOutput,
} from "../commands/SetIdentityMailFromDomainCommand";
import {
  SetIdentityNotificationTopicCommandInput,
  SetIdentityNotificationTopicCommandOutput,
} from "../commands/SetIdentityNotificationTopicCommand";
import {
  SetReceiptRulePositionCommandInput,
  SetReceiptRulePositionCommandOutput,
} from "../commands/SetReceiptRulePositionCommand";
import {
  TestRenderTemplateCommandInput,
  TestRenderTemplateCommandOutput,
} from "../commands/TestRenderTemplateCommand";
import {
  UpdateAccountSendingEnabledCommandInput,
  UpdateAccountSendingEnabledCommandOutput,
} from "../commands/UpdateAccountSendingEnabledCommand";
import {
  UpdateConfigurationSetEventDestinationCommandInput,
  UpdateConfigurationSetEventDestinationCommandOutput,
} from "../commands/UpdateConfigurationSetEventDestinationCommand";
import {
  UpdateConfigurationSetReputationMetricsEnabledCommandInput,
  UpdateConfigurationSetReputationMetricsEnabledCommandOutput,
} from "../commands/UpdateConfigurationSetReputationMetricsEnabledCommand";
import {
  UpdateConfigurationSetSendingEnabledCommandInput,
  UpdateConfigurationSetSendingEnabledCommandOutput,
} from "../commands/UpdateConfigurationSetSendingEnabledCommand";
import {
  UpdateConfigurationSetTrackingOptionsCommandInput,
  UpdateConfigurationSetTrackingOptionsCommandOutput,
} from "../commands/UpdateConfigurationSetTrackingOptionsCommand";
import {
  UpdateCustomVerificationEmailTemplateCommandInput,
  UpdateCustomVerificationEmailTemplateCommandOutput,
} from "../commands/UpdateCustomVerificationEmailTemplateCommand";
import {
  UpdateReceiptRuleCommandInput,
  UpdateReceiptRuleCommandOutput,
} from "../commands/UpdateReceiptRuleCommand";
import {
  UpdateTemplateCommandInput,
  UpdateTemplateCommandOutput,
} from "../commands/UpdateTemplateCommand";
import {
  VerifyDomainDkimCommandInput,
  VerifyDomainDkimCommandOutput,
} from "../commands/VerifyDomainDkimCommand";
import {
  VerifyDomainIdentityCommandInput,
  VerifyDomainIdentityCommandOutput,
} from "../commands/VerifyDomainIdentityCommand";
import {
  VerifyEmailAddressCommandInput,
  VerifyEmailAddressCommandOutput,
} from "../commands/VerifyEmailAddressCommand";
import {
  VerifyEmailIdentityCommandInput,
  VerifyEmailIdentityCommandOutput,
} from "../commands/VerifyEmailIdentityCommand";
export declare const se_CloneReceiptRuleSetCommand: (
  input: CloneReceiptRuleSetCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_CreateConfigurationSetCommand: (
  input: CreateConfigurationSetCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_CreateConfigurationSetEventDestinationCommand: (
  input: CreateConfigurationSetEventDestinationCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_CreateConfigurationSetTrackingOptionsCommand: (
  input: CreateConfigurationSetTrackingOptionsCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_CreateCustomVerificationEmailTemplateCommand: (
  input: CreateCustomVerificationEmailTemplateCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_CreateReceiptFilterCommand: (
  input: CreateReceiptFilterCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_CreateReceiptRuleCommand: (
  input: CreateReceiptRuleCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_CreateReceiptRuleSetCommand: (
  input: CreateReceiptRuleSetCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_CreateTemplateCommand: (
  input: CreateTemplateCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DeleteConfigurationSetCommand: (
  input: DeleteConfigurationSetCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DeleteConfigurationSetEventDestinationCommand: (
  input: DeleteConfigurationSetEventDestinationCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DeleteConfigurationSetTrackingOptionsCommand: (
  input: DeleteConfigurationSetTrackingOptionsCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DeleteCustomVerificationEmailTemplateCommand: (
  input: DeleteCustomVerificationEmailTemplateCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DeleteIdentityCommand: (
  input: DeleteIdentityCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DeleteIdentityPolicyCommand: (
  input: DeleteIdentityPolicyCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DeleteReceiptFilterCommand: (
  input: DeleteReceiptFilterCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DeleteReceiptRuleCommand: (
  input: DeleteReceiptRuleCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DeleteReceiptRuleSetCommand: (
  input: DeleteReceiptRuleSetCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DeleteTemplateCommand: (
  input: DeleteTemplateCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DeleteVerifiedEmailAddressCommand: (
  input: DeleteVerifiedEmailAddressCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DescribeActiveReceiptRuleSetCommand: (
  input: DescribeActiveReceiptRuleSetCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DescribeConfigurationSetCommand: (
  input: DescribeConfigurationSetCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DescribeReceiptRuleCommand: (
  input: DescribeReceiptRuleCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_DescribeReceiptRuleSetCommand: (
  input: DescribeReceiptRuleSetCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_GetAccountSendingEnabledCommand: (
  input: GetAccountSendingEnabledCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_GetCustomVerificationEmailTemplateCommand: (
  input: GetCustomVerificationEmailTemplateCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_GetIdentityDkimAttributesCommand: (
  input: GetIdentityDkimAttributesCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_GetIdentityMailFromDomainAttributesCommand: (
  input: GetIdentityMailFromDomainAttributesCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_GetIdentityNotificationAttributesCommand: (
  input: GetIdentityNotificationAttributesCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_GetIdentityPoliciesCommand: (
  input: GetIdentityPoliciesCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_GetIdentityVerificationAttributesCommand: (
  input: GetIdentityVerificationAttributesCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_GetSendQuotaCommand: (
  input: GetSendQuotaCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_GetSendStatisticsCommand: (
  input: GetSendStatisticsCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_GetTemplateCommand: (
  input: GetTemplateCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_ListConfigurationSetsCommand: (
  input: ListConfigurationSetsCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_ListCustomVerificationEmailTemplatesCommand: (
  input: ListCustomVerificationEmailTemplatesCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_ListIdentitiesCommand: (
  input: ListIdentitiesCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_ListIdentityPoliciesCommand: (
  input: ListIdentityPoliciesCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_ListReceiptFiltersCommand: (
  input: ListReceiptFiltersCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_ListReceiptRuleSetsCommand: (
  input: ListReceiptRuleSetsCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_ListTemplatesCommand: (
  input: ListTemplatesCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_ListVerifiedEmailAddressesCommand: (
  input: ListVerifiedEmailAddressesCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_PutConfigurationSetDeliveryOptionsCommand: (
  input: PutConfigurationSetDeliveryOptionsCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_PutIdentityPolicyCommand: (
  input: PutIdentityPolicyCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_ReorderReceiptRuleSetCommand: (
  input: ReorderReceiptRuleSetCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SendBounceCommand: (
  input: SendBounceCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SendBulkTemplatedEmailCommand: (
  input: SendBulkTemplatedEmailCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SendCustomVerificationEmailCommand: (
  input: SendCustomVerificationEmailCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SendEmailCommand: (
  input: SendEmailCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SendRawEmailCommand: (
  input: SendRawEmailCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SendTemplatedEmailCommand: (
  input: SendTemplatedEmailCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SetActiveReceiptRuleSetCommand: (
  input: SetActiveReceiptRuleSetCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SetIdentityDkimEnabledCommand: (
  input: SetIdentityDkimEnabledCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SetIdentityFeedbackForwardingEnabledCommand: (
  input: SetIdentityFeedbackForwardingEnabledCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SetIdentityHeadersInNotificationsEnabledCommand: (
  input: SetIdentityHeadersInNotificationsEnabledCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SetIdentityMailFromDomainCommand: (
  input: SetIdentityMailFromDomainCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SetIdentityNotificationTopicCommand: (
  input: SetIdentityNotificationTopicCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_SetReceiptRulePositionCommand: (
  input: SetReceiptRulePositionCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_TestRenderTemplateCommand: (
  input: TestRenderTemplateCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_UpdateAccountSendingEnabledCommand: (
  input: UpdateAccountSendingEnabledCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_UpdateConfigurationSetEventDestinationCommand: (
  input: UpdateConfigurationSetEventDestinationCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_UpdateConfigurationSetReputationMetricsEnabledCommand: (
  input: UpdateConfigurationSetReputationMetricsEnabledCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_UpdateConfigurationSetSendingEnabledCommand: (
  input: UpdateConfigurationSetSendingEnabledCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_UpdateConfigurationSetTrackingOptionsCommand: (
  input: UpdateConfigurationSetTrackingOptionsCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_UpdateCustomVerificationEmailTemplateCommand: (
  input: UpdateCustomVerificationEmailTemplateCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_UpdateReceiptRuleCommand: (
  input: UpdateReceiptRuleCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_UpdateTemplateCommand: (
  input: UpdateTemplateCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_VerifyDomainDkimCommand: (
  input: VerifyDomainDkimCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_VerifyDomainIdentityCommand: (
  input: VerifyDomainIdentityCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_VerifyEmailAddressCommand: (
  input: VerifyEmailAddressCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const se_VerifyEmailIdentityCommand: (
  input: VerifyEmailIdentityCommandInput,
  context: __SerdeContext
) => Promise<__HttpRequest>;
export declare const de_CloneReceiptRuleSetCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<CloneReceiptRuleSetCommandOutput>;
export declare const de_CreateConfigurationSetCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<CreateConfigurationSetCommandOutput>;
export declare const de_CreateConfigurationSetEventDestinationCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<CreateConfigurationSetEventDestinationCommandOutput>;
export declare const de_CreateConfigurationSetTrackingOptionsCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<CreateConfigurationSetTrackingOptionsCommandOutput>;
export declare const de_CreateCustomVerificationEmailTemplateCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<CreateCustomVerificationEmailTemplateCommandOutput>;
export declare const de_CreateReceiptFilterCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<CreateReceiptFilterCommandOutput>;
export declare const de_CreateReceiptRuleCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<CreateReceiptRuleCommandOutput>;
export declare const de_CreateReceiptRuleSetCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<CreateReceiptRuleSetCommandOutput>;
export declare const de_CreateTemplateCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<CreateTemplateCommandOutput>;
export declare const de_DeleteConfigurationSetCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DeleteConfigurationSetCommandOutput>;
export declare const de_DeleteConfigurationSetEventDestinationCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DeleteConfigurationSetEventDestinationCommandOutput>;
export declare const de_DeleteConfigurationSetTrackingOptionsCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DeleteConfigurationSetTrackingOptionsCommandOutput>;
export declare const de_DeleteCustomVerificationEmailTemplateCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DeleteCustomVerificationEmailTemplateCommandOutput>;
export declare const de_DeleteIdentityCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DeleteIdentityCommandOutput>;
export declare const de_DeleteIdentityPolicyCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DeleteIdentityPolicyCommandOutput>;
export declare const de_DeleteReceiptFilterCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DeleteReceiptFilterCommandOutput>;
export declare const de_DeleteReceiptRuleCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DeleteReceiptRuleCommandOutput>;
export declare const de_DeleteReceiptRuleSetCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DeleteReceiptRuleSetCommandOutput>;
export declare const de_DeleteTemplateCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DeleteTemplateCommandOutput>;
export declare const de_DeleteVerifiedEmailAddressCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DeleteVerifiedEmailAddressCommandOutput>;
export declare const de_DescribeActiveReceiptRuleSetCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DescribeActiveReceiptRuleSetCommandOutput>;
export declare const de_DescribeConfigurationSetCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DescribeConfigurationSetCommandOutput>;
export declare const de_DescribeReceiptRuleCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DescribeReceiptRuleCommandOutput>;
export declare const de_DescribeReceiptRuleSetCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<DescribeReceiptRuleSetCommandOutput>;
export declare const de_GetAccountSendingEnabledCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<GetAccountSendingEnabledCommandOutput>;
export declare const de_GetCustomVerificationEmailTemplateCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<GetCustomVerificationEmailTemplateCommandOutput>;
export declare const de_GetIdentityDkimAttributesCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<GetIdentityDkimAttributesCommandOutput>;
export declare const de_GetIdentityMailFromDomainAttributesCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<GetIdentityMailFromDomainAttributesCommandOutput>;
export declare const de_GetIdentityNotificationAttributesCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<GetIdentityNotificationAttributesCommandOutput>;
export declare const de_GetIdentityPoliciesCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<GetIdentityPoliciesCommandOutput>;
export declare const de_GetIdentityVerificationAttributesCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<GetIdentityVerificationAttributesCommandOutput>;
export declare const de_GetSendQuotaCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<GetSendQuotaCommandOutput>;
export declare const de_GetSendStatisticsCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<GetSendStatisticsCommandOutput>;
export declare const de_GetTemplateCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<GetTemplateCommandOutput>;
export declare const de_ListConfigurationSetsCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<ListConfigurationSetsCommandOutput>;
export declare const de_ListCustomVerificationEmailTemplatesCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<ListCustomVerificationEmailTemplatesCommandOutput>;
export declare const de_ListIdentitiesCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<ListIdentitiesCommandOutput>;
export declare const de_ListIdentityPoliciesCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<ListIdentityPoliciesCommandOutput>;
export declare const de_ListReceiptFiltersCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<ListReceiptFiltersCommandOutput>;
export declare const de_ListReceiptRuleSetsCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<ListReceiptRuleSetsCommandOutput>;
export declare const de_ListTemplatesCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<ListTemplatesCommandOutput>;
export declare const de_ListVerifiedEmailAddressesCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<ListVerifiedEmailAddressesCommandOutput>;
export declare const de_PutConfigurationSetDeliveryOptionsCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<PutConfigurationSetDeliveryOptionsCommandOutput>;
export declare const de_PutIdentityPolicyCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<PutIdentityPolicyCommandOutput>;
export declare const de_ReorderReceiptRuleSetCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<ReorderReceiptRuleSetCommandOutput>;
export declare const de_SendBounceCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SendBounceCommandOutput>;
export declare const de_SendBulkTemplatedEmailCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SendBulkTemplatedEmailCommandOutput>;
export declare const de_SendCustomVerificationEmailCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SendCustomVerificationEmailCommandOutput>;
export declare const de_SendEmailCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SendEmailCommandOutput>;
export declare const de_SendRawEmailCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SendRawEmailCommandOutput>;
export declare const de_SendTemplatedEmailCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SendTemplatedEmailCommandOutput>;
export declare const de_SetActiveReceiptRuleSetCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SetActiveReceiptRuleSetCommandOutput>;
export declare const de_SetIdentityDkimEnabledCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SetIdentityDkimEnabledCommandOutput>;
export declare const de_SetIdentityFeedbackForwardingEnabledCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SetIdentityFeedbackForwardingEnabledCommandOutput>;
export declare const de_SetIdentityHeadersInNotificationsEnabledCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SetIdentityHeadersInNotificationsEnabledCommandOutput>;
export declare const de_SetIdentityMailFromDomainCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SetIdentityMailFromDomainCommandOutput>;
export declare const de_SetIdentityNotificationTopicCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SetIdentityNotificationTopicCommandOutput>;
export declare const de_SetReceiptRulePositionCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<SetReceiptRulePositionCommandOutput>;
export declare const de_TestRenderTemplateCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<TestRenderTemplateCommandOutput>;
export declare const de_UpdateAccountSendingEnabledCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<UpdateAccountSendingEnabledCommandOutput>;
export declare const de_UpdateConfigurationSetEventDestinationCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<UpdateConfigurationSetEventDestinationCommandOutput>;
export declare const de_UpdateConfigurationSetReputationMetricsEnabledCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<UpdateConfigurationSetReputationMetricsEnabledCommandOutput>;
export declare const de_UpdateConfigurationSetSendingEnabledCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<UpdateConfigurationSetSendingEnabledCommandOutput>;
export declare const de_UpdateConfigurationSetTrackingOptionsCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<UpdateConfigurationSetTrackingOptionsCommandOutput>;
export declare const de_UpdateCustomVerificationEmailTemplateCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<UpdateCustomVerificationEmailTemplateCommandOutput>;
export declare const de_UpdateReceiptRuleCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<UpdateReceiptRuleCommandOutput>;
export declare const de_UpdateTemplateCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<UpdateTemplateCommandOutput>;
export declare const de_VerifyDomainDkimCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<VerifyDomainDkimCommandOutput>;
export declare const de_VerifyDomainIdentityCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<VerifyDomainIdentityCommandOutput>;
export declare const de_VerifyEmailAddressCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<VerifyEmailAddressCommandOutput>;
export declare const de_VerifyEmailIdentityCommand: (
  output: __HttpResponse,
  context: __SerdeContext
) => Promise<VerifyEmailIdentityCommandOutput>;
