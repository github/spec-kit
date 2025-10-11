import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  GetCustomVerificationEmailTemplateRequest,
  GetCustomVerificationEmailTemplateResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface GetCustomVerificationEmailTemplateCommandInput
  extends GetCustomVerificationEmailTemplateRequest {}
export interface GetCustomVerificationEmailTemplateCommandOutput
  extends GetCustomVerificationEmailTemplateResponse,
    __MetadataBearer {}
declare const GetCustomVerificationEmailTemplateCommand_base: {
  new (
    input: GetCustomVerificationEmailTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetCustomVerificationEmailTemplateCommandInput,
    GetCustomVerificationEmailTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: GetCustomVerificationEmailTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetCustomVerificationEmailTemplateCommandInput,
    GetCustomVerificationEmailTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class GetCustomVerificationEmailTemplateCommand extends GetCustomVerificationEmailTemplateCommand_base {
  protected static __types: {
    api: {
      input: GetCustomVerificationEmailTemplateRequest;
      output: GetCustomVerificationEmailTemplateResponse;
    };
    sdk: {
      input: GetCustomVerificationEmailTemplateCommandInput;
      output: GetCustomVerificationEmailTemplateCommandOutput;
    };
  };
}
