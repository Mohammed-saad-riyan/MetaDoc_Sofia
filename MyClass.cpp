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
        // Add a small buffer (0.05s) to ensure we've truly reached the end
        if (ElapsedTime > JawKeyframes.Last().Time + 0.05f)
        {
            // Animation is complete, set flags for next request
            bUseJsonAnimation = false;
            bAnimationCompleted = true;
            ResetAnimationValues();
            UE_LOG(LogTemp, Display, TEXT("Animation completed at %f seconds (last keyframe: %f)"),
                ElapsedTime, JawKeyframes.Last().Time);
            return;
        }
        
        // Find the current and next keyframes
        int32 CurrentIndex = 0;
        int32 NextIndex = 0;
        bool bFoundCurrent = false;
        
        // Improved keyframe searching - find the keyframes that bracket our current time
        for (int32 i = 0; i < JawKeyframes.Num() - 1; i++)
        {
            if (ElapsedTime >= JawKeyframes[i].Time && ElapsedTime < JawKeyframes[i + 1].Time)
            {
                CurrentIndex = i;
                NextIndex = i + 1;
                bFoundCurrent = true;
                break;
            }
        }
        
        // If we didn't find a bracket, check if we're at or past the last keyframe
        if (!bFoundCurrent)
        {
            if (ElapsedTime >= JawKeyframes.Last().Time)
            {
                // We're past the last keyframe - use the last two keyframes
                CurrentIndex = JawKeyframes.Num() - 2;
                NextIndex = JawKeyframes.Num() - 1;
                
                // If we're significantly past the last keyframe, stop animation
                if (ElapsedTime > JawKeyframes.Last().Time + 0.1f)
                {
                    bUseJsonAnimation = false;
                    bAnimationCompleted = true;
                    ResetAnimationValues();
                    UE_LOG(LogTemp, Display, TEXT("Animation ended - past last keyframe %f"), JawKeyframes.Last().Time);
                    return;
                }
            }
            else
            {
                // We're before the first keyframe - use the first two keyframes
                CurrentIndex = 0;
                NextIndex = FMath::Min(1, JawKeyframes.Num() - 1);
            }
        }
        
        // Check if we've reached the "rest" phase or end of audio
        // Check for speech_end_time in the JSON data
        bool bIsRestingPhase = false;
        if (bJsonHasSpeechEndTime && ElapsedTime >= JsonSpeechEndTime && JawKeyframes[CurrentIndex].JawValue.Y < 0.05f)
        {
            // We're past speech end and jaw is nearly closed
            bIsRestingPhase = true;
            
            // If we're fully closed and well past speech end, accelerate the ending
            if (JawKeyframes[CurrentIndex].JawValue.Y < 0.02f && ElapsedTime > JsonSpeechEndTime + 0.3f)
            {
                // Quickly progress to fully closed
                JawOpenValue = FVector::ZeroVector;
                FunnelRightUp = 0.0f;
                FunnelRightDown = 0.0f;
                FunnelLeftUp = 0.0f;
                FunnelLeftDown = 0.0f;
                PurseRightUp = 0.0f;
                PurseRightDown = 0.0f;
                PurseLeftUp = 0.0f;
                PurseLeftDown = 0.0f;
                CornerPullRight = 0.0f;
                CornerPullLeft = 0.0f;
                TeethUpperValue = FVector::ZeroVector;
                TeethLowerValue = FVector::ZeroVector;
                TongueValue = FVector::ZeroVector;
                TongueInOut = 0.0f;
                PressRightUp = 0.0f;
                PressRightDown = 0.0f;
                PressLeftUp = 0.0f;
                PressLeftDown = 0.0f;
                TowardsRightUp = 0.0f;
                TowardsRightDown = 0.0f;
                TowardsLeftUp = 0.0f;
                TowardsLeftDown = 0.0f;
                
                // If nearly half a second past speech end, just end animation
                if (ElapsedTime > JsonSpeechEndTime + 0.5f)
                {
                    bUseJsonAnimation = false;
                    bAnimationCompleted = true;
                    ResetAnimationValues();
                    UE_LOG(LogTemp, Display, TEXT("Animation ended naturally at rest state"));
                    return;
                }
                
                // Skip further processing
                return;
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
            // Clamp alpha to [0,1] range
            Alpha = FMath::Clamp(Alpha, 0.0f, 1.0f);
            
            // Use smoother interpolation curve (ease-in-out)
            // Use stronger easing for rest phases
            if (bIsRestingPhase)
            {
                // Stronger ease-out for resting phase
                Alpha = 1.0f - FMath::Pow(1.0f - Alpha, 3.0f);
            }
            else
            {
                // Normal ease-in-out for speaking
                Alpha = Alpha * Alpha * (3.0f - 2.0f * Alpha);
            }
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
                // If server provides a specific JSON file path, use it
                if (JsonObject->HasField("json_file_path") && !JsonObject->GetStringField("json_file_path").IsEmpty())
                {
                    FString ServerProvidedPath = JsonObject->GetStringField("json_file_path");
                    UE_LOG(LogTemp, Display, TEXT("Using server-provided JSON path: %s"), *ServerProvidedPath);
                    
                    // Update the JsonFilePath with the server-provided path
                    JsonFilePath = ServerProvidedPath;
                    
                    // Load the animation data from the new path
                    LoadJawAnimationData();
                }
                
                // Reset elapsed time when starting animation
                ElapsedTime = 0.0f;
                bUseJsonAnimation = true;
                bAnimationCompleted = false;
                UE_LOG(LogTemp, Display, TEXT("Starting facial animation from JSON: %s"), *JsonFilePath);
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
    
    // Reset speech end time flag
    bJsonHasSpeechEndTime = false;
    JsonSpeechEndTime = 0.0f;
    
    UE_LOG(LogTemp, Display, TEXT("Attempting to load JSON animation from: %s"), *JsonFilePath);
    
    // Read the JSON file - using the absolute path provided
    FString JsonString;
    if (FFileHelper::LoadFileToString(JsonString, *JsonFilePath))
    {
        UE_LOG(LogTemp, Display, TEXT("Successfully read JSON file, size: %d bytes"), JsonString.Len());
        
        TSharedPtr<FJsonObject> JsonObject;
        TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);
        
        if (FJsonSerializer::Deserialize(Reader, JsonObject) && JsonObject.IsValid())
        {
            // Check if JSON has a duration field
            if (JsonObject->HasField("duration"))
            {
                double FileDuration = JsonObject->GetNumberField("duration");
                UE_LOG(LogTemp, Display, TEXT("Animation duration from JSON: %f seconds"), FileDuration);
            }
            
            // Check for speech_end_time field - very important for smooth endings
            if (JsonObject->HasField("speech_end_time"))
            {
                JsonSpeechEndTime = JsonObject->GetNumberField("speech_end_time");
                bJsonHasSpeechEndTime = true;
                UE_LOG(LogTemp, Display, TEXT("Speech ends at: %f seconds"), JsonSpeechEndTime);
            }
            
            // Parse the keyframes array
            if (JsonObject->HasField("keyframes"))
            {
                TArray<TSharedPtr<FJsonValue>> KeyframesArray = JsonObject->GetArrayField("keyframes");
                UE_LOG(LogTemp, Display, TEXT("Found %d keyframes in JSON"), KeyframesArray.Num());
                
                float LastTime = -1.0f; // For checking keyframe ordering
                
                for (const TSharedPtr<FJsonValue>& KeyframeValue : KeyframesArray)
                {
                    TSharedPtr<FJsonObject> KeyframeObject = KeyframeValue->AsObject();
                    
                    if (KeyframeObject.IsValid())
                    {
                        // Create a new keyframe
                        FJawKeyframe Keyframe;
                        
                        // Parse time
                        Keyframe.Time = KeyframeObject->GetNumberField("time");
                        
                        // Check for time monotonicity
                        if (Keyframe.Time <= LastTime)
                        {
                            UE_LOG(LogTemp, Warning, TEXT("Non-monotonic keyframe times: %f after %f"), Keyframe.Time, LastTime);
                        }
                        LastTime = Keyframe.Time;
                        
                        // Parse phoneme if available (for debugging)
                        if (KeyframeObject->HasField("phoneme"))
                        {
                            FString Phoneme = KeyframeObject->GetStringField("phoneme");
                            if (Phoneme == "rest" && Keyframe.Time > 0.0f)
                            {
                                UE_LOG(LogTemp, Display, TEXT("Rest phoneme at time %f"), Keyframe.Time);
                            }
                        }
                        
                        // Parse jaw values
                        if (KeyframeObject->HasField("jawValue"))
                        {
                            TSharedPtr<FJsonObject> JawObject = KeyframeObject->GetObjectField("jawValue");
                            Keyframe.JawValue.X = JawObject->GetNumberField("x");
                            Keyframe.JawValue.Y = JawObject->GetNumberField("y");
                            Keyframe.JawValue.Z = JawObject->GetNumberField("z");
                        }
                        else
                        {
                            // Set default values if not present
                            Keyframe.JawValue = FVector::ZeroVector;
                            UE_LOG(LogTemp, Warning, TEXT("Keyframe at %f missing jawValue"), Keyframe.Time);
                        }
                        
                        // Parse funnel values
                        Keyframe.FunnelRightUp = KeyframeObject->HasField("funnelRightUp") ? KeyframeObject->GetNumberField("funnelRightUp") : 0.0f;
                        Keyframe.FunnelRightDown = KeyframeObject->HasField("funnelRightDown") ? KeyframeObject->GetNumberField("funnelRightDown") : 0.0f;
                        Keyframe.FunnelLeftUp = KeyframeObject->HasField("funnelLeftUp") ? KeyframeObject->GetNumberField("funnelLeftUp") : 0.0f;
                        Keyframe.FunnelLeftDown = KeyframeObject->HasField("funnelLeftDown") ? KeyframeObject->GetNumberField("funnelLeftDown") : 0.0f;
                        
                        // Parse purse values
                        Keyframe.PurseRightUp = KeyframeObject->HasField("purseRightUp") ? KeyframeObject->GetNumberField("purseRightUp") : 0.0f;
                        Keyframe.PurseRightDown = KeyframeObject->HasField("purseRightDown") ? KeyframeObject->GetNumberField("purseRightDown") : 0.0f;
                        Keyframe.PurseLeftUp = KeyframeObject->HasField("purseLeftUp") ? KeyframeObject->GetNumberField("purseLeftUp") : 0.0f;
                        Keyframe.PurseLeftDown = KeyframeObject->HasField("purseLeftDown") ? KeyframeObject->GetNumberField("purseLeftDown") : 0.0f;
                        
                        // Parse corner pull values
                        Keyframe.CornerPullRight = KeyframeObject->HasField("cornerPullRight") ? KeyframeObject->GetNumberField("cornerPullRight") : 0.0f;
                        Keyframe.CornerPullLeft = KeyframeObject->HasField("cornerPullLeft") ? KeyframeObject->GetNumberField("cornerPullLeft") : 0.0f;
                        
                        // Parse teeth values
                        if (KeyframeObject->HasField("teethUpperValue"))
                        {
                            TSharedPtr<FJsonObject> TeethUpperObject = KeyframeObject->GetObjectField("teethUpperValue");
                            Keyframe.TeethUpperValue.X = TeethUpperObject->GetNumberField("x");
                            Keyframe.TeethUpperValue.Y = TeethUpperObject->GetNumberField("y");
                            Keyframe.TeethUpperValue.Z = TeethUpperObject->GetNumberField("z");
                        }
                        else
                        {
                            Keyframe.TeethUpperValue = FVector::ZeroVector;
                        }
                        
                        if (KeyframeObject->HasField("teethLowerValue"))
                        {
                            TSharedPtr<FJsonObject> TeethLowerObject = KeyframeObject->GetObjectField("teethLowerValue");
                            Keyframe.TeethLowerValue.X = TeethLowerObject->GetNumberField("x");
                            Keyframe.TeethLowerValue.Y = TeethLowerObject->GetNumberField("y");
                            Keyframe.TeethLowerValue.Z = TeethLowerObject->GetNumberField("z");
                        }
                        else
                        {
                            Keyframe.TeethLowerValue = FVector::ZeroVector;
                        }
                        
                        // Parse tongue values
                        if (KeyframeObject->HasField("tongueValue"))
                        {
                            TSharedPtr<FJsonObject> TongueObject = KeyframeObject->GetObjectField("tongueValue");
                            Keyframe.TongueValue.X = TongueObject->GetNumberField("x");
                            Keyframe.TongueValue.Y = TongueObject->GetNumberField("y");
                            Keyframe.TongueValue.Z = TongueObject->GetNumberField("z");
                        }
                        else
                        {
                            Keyframe.TongueValue = FVector::ZeroVector;
                        }
                        
                        Keyframe.TongueInOut = KeyframeObject->HasField("tongueInOut") ? KeyframeObject->GetNumberField("tongueInOut") : 0.0f;
                        
                        // Parse press values
                        Keyframe.PressRightUp = KeyframeObject->HasField("pressRightUp") ? KeyframeObject->GetNumberField("pressRightUp") : 0.0f;
                        Keyframe.PressRightDown = KeyframeObject->HasField("pressRightDown") ? KeyframeObject->GetNumberField("pressRightDown") : 0.0f;
                        Keyframe.PressLeftUp = KeyframeObject->HasField("pressLeftUp") ? KeyframeObject->GetNumberField("pressLeftUp") : 0.0f;
                        Keyframe.PressLeftDown = KeyframeObject->HasField("pressLeftDown") ? KeyframeObject->GetNumberField("pressLeftDown") : 0.0f;
                        
                        // Parse towards values
                        Keyframe.TowardsRightUp = KeyframeObject->HasField("towardsRightUp") ? KeyframeObject->GetNumberField("towardsRightUp") : 0.0f;
                        Keyframe.TowardsRightDown = KeyframeObject->HasField("towardsRightDown") ? KeyframeObject->GetNumberField("towardsRightDown") : 0.0f;
                        Keyframe.TowardsLeftUp = KeyframeObject->HasField("towardsLeftUp") ? KeyframeObject->GetNumberField("towardsLeftUp") : 0.0f;
                        Keyframe.TowardsLeftDown = KeyframeObject->HasField("towardsLeftDown") ? KeyframeObject->GetNumberField("towardsLeftDown") : 0.0f;
                        
                        // Add to our keyframes array
                        JawKeyframes.Add(Keyframe);
                    }
                }
                
                // Sort keyframes by time
                JawKeyframes.Sort([](const FJawKeyframe& A, const FJawKeyframe& B) {
                    return A.Time < B.Time;
                });
                
                UE_LOG(LogTemp, Display, TEXT("Loaded %d facial animation keyframes from JSON"), JawKeyframes.Num());
                if (JawKeyframes.Num() > 0)
                {
                    UE_LOG(LogTemp, Display, TEXT("Animation time range: %f to %f seconds"),
                        JawKeyframes[0].Time, JawKeyframes.Last().Time);
                    
                    // Log every 10th keyframe for verification
                    for (int32 i = 0; i < JawKeyframes.Num(); i += FMath::Max(1, JawKeyframes.Num() / 10))
                    {
                        UE_LOG(LogTemp, Display, TEXT("Keyframe[%d]: Time=%f, JawY=%f"),
                            i, JawKeyframes[i].Time, JawKeyframes[i].JawValue.Y);
                    }
                }
                else
                {
                    UE_LOG(LogTemp, Warning, TEXT("No keyframes found in JSON file"));
                }
            }
            else
            {
                UE_LOG(LogTemp, Warning, TEXT("JSON file does not contain 'keyframes' array"));
            }
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
