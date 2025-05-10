#include "MyClass.h"
#include "JsonObjectConverter.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformFileManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"

void UMyClass::NativeInitializeAnimation()
{
    Super::NativeInitializeAnimation();
    
    ElapsedTime = 0.0f;
    
    // Initialize all animation values to zero
    ResetAnimationValues();
    
    // Initialize HTTP module
    if (!FHttpModule::Get().IsHttpEnabled())
    {
        UE_LOG(LogTemp, Error, TEXT("HTTP module is not enabled"));
    }
    
    // Load the animation data from JSON but don't use it yet
    LoadJawAnimationData();
    
    // Initially don't use jaw values from JSON
    bUseJsonAnimation = false;
    
    // Set up server checking
    LastPollTime = 0.0f;
    
    // Flag to track if we need to make a new request after animation completes
    bAnimationCompleted = false;
}

void UMyClass::ResetAnimationValues()
{
    // Reset all animation values to zero
    JawOpenValue = FVector::ZeroVector;
    
    // Funnel values
    FunnelRightUp = 0.0f;
    FunnelRightDown = 0.0f;
    FunnelLeftUp = 0.0f;
    FunnelLeftDown = 0.0f;
    
    // Purse values
    PurseRightUp = 0.0f;
    PurseRightDown = 0.0f;
    PurseLeftUp = 0.0f;
    PurseLeftDown = 0.0f;
    
    // Corner pull values
    CornerPullRight = 0.0f;
    CornerPullLeft = 0.0f;
    
    // Teeth values
    TeethUpperValue = FVector::ZeroVector;
    TeethLowerValue = FVector::ZeroVector;
    
    // Tongue values
    TongueValue = FVector::ZeroVector;
    TongueInOut = 0.0f;
    
    // Press values
    PressRightUp = 0.0f;
    PressRightDown = 0.0f;
    PressLeftUp = 0.0f;
    PressLeftDown = 0.0f;
    
    // Towards values
    TowardsRightUp = 0.0f;
    TowardsRightDown = 0.0f;
    TowardsLeftUp = 0.0f;
    TowardsLeftDown = 0.0f;
}

void UMyClass::NativeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeUpdateAnimation(DeltaSeconds);

    // Check if we need to make a new request after animation completion
    if (bAnimationCompleted)
    {
        CheckServer();
        bAnimationCompleted = false;
        return;
    }

    // Update elapsed time
    ElapsedTime += DeltaSeconds;
    
    // Check if it's time to poll the server
    // Only poll if we're not currently animating
    if (!bUseJsonAnimation)
    {
        LastPollTime += DeltaSeconds;
        if (LastPollTime >= PollInterval)
        {
            CheckServer();
            LastPollTime = 0.0f;
        }
    }
    
    // Only use JSON animation if we've received a response from the server
    if (bUseJsonAnimation && JawKeyframes.Num() > 0)
    {
        // Check if animation has completed (reached or passed the last keyframe)
        if (ElapsedTime > JawKeyframes.Last().Time)
        {
            // Animation is complete, set flags for next request
            bUseJsonAnimation = false;
            bAnimationCompleted = true;
            ResetAnimationValues();
            UE_LOG(LogTemp, Display, TEXT("Animation completed, will make new request"));
            return;
        }
        
        // Find the current and next keyframes
        int32 CurrentIndex = 0;
        int32 NextIndex = 0;
        
        for (int32 i = 0; i < JawKeyframes.Num(); i++)
        {
            if (ElapsedTime >= JawKeyframes[i].Time)
            {
                CurrentIndex = i;
            }
            else
            {
                NextIndex = i;
                break;
            }
        }
        
        // Interpolate between current and next keyframe
        const FJawKeyframe& CurrentKeyframe = JawKeyframes[CurrentIndex];
        const FJawKeyframe& NextKeyframe = JawKeyframes[NextIndex];
        
        float StartTime = CurrentKeyframe.Time;
        float EndTime = NextKeyframe.Time;
        
        float Alpha = 0.0f;
        if (EndTime != StartTime) // Prevent division by zero
        {
            Alpha = (ElapsedTime - StartTime) / (EndTime - StartTime);
        }
        
        // Interpolate all facial values
        
        // Jaw values
        JawOpenValue = FMath::Lerp(CurrentKeyframe.JawValue, NextKeyframe.JawValue, Alpha);
        
        // Funnel values
        FunnelRightUp = FMath::Lerp(CurrentKeyframe.FunnelRightUp, NextKeyframe.FunnelRightUp, Alpha);
        FunnelRightDown = FMath::Lerp(CurrentKeyframe.FunnelRightDown, NextKeyframe.FunnelRightDown, Alpha);
        FunnelLeftUp = FMath::Lerp(CurrentKeyframe.FunnelLeftUp, NextKeyframe.FunnelLeftUp, Alpha);
        FunnelLeftDown = FMath::Lerp(CurrentKeyframe.FunnelLeftDown, NextKeyframe.FunnelLeftDown, Alpha);
        
        // Purse values
        PurseRightUp = FMath::Lerp(CurrentKeyframe.PurseRightUp, NextKeyframe.PurseRightUp, Alpha);
        PurseRightDown = FMath::Lerp(CurrentKeyframe.PurseRightDown, NextKeyframe.PurseRightDown, Alpha);
        PurseLeftUp = FMath::Lerp(CurrentKeyframe.PurseLeftUp, NextKeyframe.PurseLeftUp, Alpha);
        PurseLeftDown = FMath::Lerp(CurrentKeyframe.PurseLeftDown, NextKeyframe.PurseLeftDown, Alpha);
        
        // Corner pull values
        CornerPullRight = FMath::Lerp(CurrentKeyframe.CornerPullRight, NextKeyframe.CornerPullRight, Alpha);
        CornerPullLeft = FMath::Lerp(CurrentKeyframe.CornerPullLeft, NextKeyframe.CornerPullLeft, Alpha);
        
        // Teeth values
        TeethUpperValue = FMath::Lerp(CurrentKeyframe.TeethUpperValue, NextKeyframe.TeethUpperValue, Alpha);
        TeethLowerValue = FMath::Lerp(CurrentKeyframe.TeethLowerValue, NextKeyframe.TeethLowerValue, Alpha);
        
        // Tongue values
        TongueValue = FMath::Lerp(CurrentKeyframe.TongueValue, NextKeyframe.TongueValue, Alpha);
        TongueInOut = FMath::Lerp(CurrentKeyframe.TongueInOut, NextKeyframe.TongueInOut, Alpha);
        
        // Press values
        PressRightUp = FMath::Lerp(CurrentKeyframe.PressRightUp, NextKeyframe.PressRightUp, Alpha);
        PressRightDown = FMath::Lerp(CurrentKeyframe.PressRightDown, NextKeyframe.PressRightDown, Alpha);
        PressLeftUp = FMath::Lerp(CurrentKeyframe.PressLeftUp, NextKeyframe.PressLeftUp, Alpha);
        PressLeftDown = FMath::Lerp(CurrentKeyframe.PressLeftDown, NextKeyframe.PressLeftDown, Alpha);
        
        // Towards values
        TowardsRightUp = FMath::Lerp(CurrentKeyframe.TowardsRightUp, NextKeyframe.TowardsRightUp, Alpha);
        TowardsRightDown = FMath::Lerp(CurrentKeyframe.TowardsRightDown, NextKeyframe.TowardsRightDown, Alpha);
        TowardsLeftUp = FMath::Lerp(CurrentKeyframe.TowardsLeftUp, NextKeyframe.TowardsLeftUp, Alpha);
        TowardsLeftDown = FMath::Lerp(CurrentKeyframe.TowardsLeftDown, NextKeyframe.TowardsLeftDown, Alpha);
    }
    else if (!bAnimationCompleted)
    {
        // Keep all values at zero until server response is received
        ResetAnimationValues();
    }
}

void UMyClass::CheckServer()
{
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
    HttpRequest->SetURL(ServerURL);
    HttpRequest->SetVerb(TEXT("GET"));
    HttpRequest->OnProcessRequestComplete().BindUObject(this, &UMyClass::OnServerResponse);
    HttpRequest->ProcessRequest();
}

void UMyClass::OnServerResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (!bWasSuccessful || !Response.IsValid())
    {
        UE_LOG(LogTemp, Warning, TEXT("Failed to connect to Flask server"));
        return;
    }
    
    if (Response->GetResponseCode() != 200)
    {
        UE_LOG(LogTemp, Warning, TEXT("Server returned error code: %d"), Response->GetResponseCode());
        return;
    }
    
    FString ResponseString = Response->GetContentAsString();
    
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseString);
    
    if (FJsonSerializer::Deserialize(Reader, JsonObject) && JsonObject.IsValid())
    {
        // Check if server wants to start animation
        if (JsonObject->HasField("start_animation"))
        {
            bool ShouldStartAnimation = JsonObject->GetBoolField("start_animation");
            
            if (ShouldStartAnimation)
            {
                // Reset elapsed time when starting animation
                ElapsedTime = 0.0f;
                bUseJsonAnimation = true;
                bAnimationCompleted = false;
                UE_LOG(LogTemp, Display, TEXT("Starting facial animation from JSON"));
            }
            else
            {
                bUseJsonAnimation = false;
                ResetAnimationValues();
                UE_LOG(LogTemp, Display, TEXT("Stopping facial animation"));
            }
        }
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("Failed to parse server response as JSON"));
    }
}

void UMyClass::LoadJawAnimationData()
{
    // Clear existing keyframes
    JawKeyframes.Empty();
    
    // Read the JSON file - using the absolute path provided
    FString JsonString;
    if (FFileHelper::LoadFileToString(JsonString, *JsonFilePath))
    {
        TSharedPtr<FJsonObject> JsonObject;
        TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);
        
        if (FJsonSerializer::Deserialize(Reader, JsonObject) && JsonObject.IsValid())
        {
            // Parse the keyframes array
            TArray<TSharedPtr<FJsonValue>> KeyframesArray = JsonObject->GetArrayField("keyframes");
            
            for (const TSharedPtr<FJsonValue>& KeyframeValue : KeyframesArray)
            {
                TSharedPtr<FJsonObject> KeyframeObject = KeyframeValue->AsObject();
                
                if (KeyframeObject.IsValid())
                {
                    // Create a new keyframe
                    FJawKeyframe Keyframe;
                    
                    // Parse time
                    Keyframe.Time = KeyframeObject->GetNumberField("time");
                    
                    // Parse jaw values
                    TSharedPtr<FJsonObject> JawObject = KeyframeObject->GetObjectField("jawValue");
                    Keyframe.JawValue.X = JawObject->GetNumberField("x");
                    Keyframe.JawValue.Y = JawObject->GetNumberField("y");
                    Keyframe.JawValue.Z = JawObject->GetNumberField("z");
                    
                    // Parse funnel values
                    Keyframe.FunnelRightUp = KeyframeObject->GetNumberField("funnelRightUp");
                    Keyframe.FunnelRightDown = KeyframeObject->GetNumberField("funnelRightDown");
                    Keyframe.FunnelLeftUp = KeyframeObject->GetNumberField("funnelLeftUp");
                    Keyframe.FunnelLeftDown = KeyframeObject->GetNumberField("funnelLeftDown");
                    
                    // Parse purse values
                    Keyframe.PurseRightUp = KeyframeObject->GetNumberField("purseRightUp");
                    Keyframe.PurseRightDown = KeyframeObject->GetNumberField("purseRightDown");
                    Keyframe.PurseLeftUp = KeyframeObject->GetNumberField("purseLeftUp");
                    Keyframe.PurseLeftDown = KeyframeObject->GetNumberField("purseLeftDown");
                    
                    // Parse corner pull values
                    Keyframe.CornerPullRight = KeyframeObject->GetNumberField("cornerPullRight");
                    Keyframe.CornerPullLeft = KeyframeObject->GetNumberField("cornerPullLeft");
                    
                    // Parse teeth values
                    TSharedPtr<FJsonObject> TeethUpperObject = KeyframeObject->GetObjectField("teethUpperValue");
                    Keyframe.TeethUpperValue.X = TeethUpperObject->GetNumberField("x");
                    Keyframe.TeethUpperValue.Y = TeethUpperObject->GetNumberField("y");
                    Keyframe.TeethUpperValue.Z = TeethUpperObject->GetNumberField("z");
                    
                    TSharedPtr<FJsonObject> TeethLowerObject = KeyframeObject->GetObjectField("teethLowerValue");
                    Keyframe.TeethLowerValue.X = TeethLowerObject->GetNumberField("x");
                    Keyframe.TeethLowerValue.Y = TeethLowerObject->GetNumberField("y");
                    Keyframe.TeethLowerValue.Z = TeethLowerObject->GetNumberField("z");
                    
                    // Parse tongue values
                    TSharedPtr<FJsonObject> TongueObject = KeyframeObject->GetObjectField("tongueValue");
                    Keyframe.TongueValue.X = TongueObject->GetNumberField("x");
                    Keyframe.TongueValue.Y = TongueObject->GetNumberField("y");
                    Keyframe.TongueValue.Z = TongueObject->GetNumberField("z");
                    
                    Keyframe.TongueInOut = KeyframeObject->GetNumberField("tongueInOut");
                    
                    // Parse press values
                    Keyframe.PressRightUp = KeyframeObject->GetNumberField("pressRightUp");
                    Keyframe.PressRightDown = KeyframeObject->GetNumberField("pressRightDown");
                    Keyframe.PressLeftUp = KeyframeObject->GetNumberField("pressLeftUp");
                    Keyframe.PressLeftDown = KeyframeObject->GetNumberField("pressLeftDown");
                    
                    // Parse towards values
                    Keyframe.TowardsRightUp = KeyframeObject->GetNumberField("towardsRightUp");
                    Keyframe.TowardsRightDown = KeyframeObject->GetNumberField("towardsRightDown");
                    Keyframe.TowardsLeftUp = KeyframeObject->GetNumberField("towardsLeftUp");
                    Keyframe.TowardsLeftDown = KeyframeObject->GetNumberField("towardsLeftDown");
                    
                    // Add to our keyframes array
                    JawKeyframes.Add(Keyframe);
                }
            }
            
            // Sort keyframes by time
            JawKeyframes.Sort([](const FJawKeyframe& A, const FJawKeyframe& B) {
                return A.Time < B.Time;
            });
            
            UE_LOG(LogTemp, Display, TEXT("Loaded %d facial animation keyframes from JSON"), JawKeyframes.Num());
        }
        else
        {
            UE_LOG(LogTemp, Warning, TEXT("Failed to parse animation JSON file"));
        }
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("Failed to load JSON file from path: %s"), *JsonFilePath);
    }
}
