import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  DeleteConfigurationSetTrackingOptionsRequest,
  DeleteConfigurationSetTrackingOptionsResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DeleteConfigurationSetTrackingOptionsCommandInput
  extends DeleteConfigurationSetTrackingOptionsRequest {}
export interface DeleteConfigurationSetTrackingOptionsCommandOutput
  extends DeleteConfigurationSetTrackingOptionsResponse,
    __MetadataBearer {}
declare const DeleteConfigurationSetTrackingOptionsCommand_base: {
  new (
    input: DeleteConfigurationSetTrackingOptionsCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteConfigurationSetTrackingOptionsCommandInput,
    DeleteConfigurationSetTrackingOptionsCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: DeleteConfigurationSetTrackingOptionsCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteConfigurationSetTrackingOptionsCommandInput,
    DeleteConfigurationSetTrackingOptionsCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DeleteConfigurationSetTrackingOptionsCommand extends DeleteConfigurationSetTrackingOptionsCommand_base {
  protected static __types: {
    api: {
      input: DeleteConfigurationSetTrackingOptionsRequest;
      output: {};
    };
    sdk: {
      input: DeleteConfigurationSetTrackingOptionsCommandInput;
      output: DeleteConfigurationSetTrackingOptionsCommandOutput;
    };
  };
}
