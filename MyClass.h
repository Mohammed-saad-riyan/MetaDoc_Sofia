#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Http.h"
#include "MyClass.generated.h"

// Structure to hold a keyframe for facial animation
USTRUCT()
struct FJawKeyframe
{
    GENERATED_BODY()
    
    // Time in seconds
    UPROPERTY()
    float Time = 0.0f;
    
    // Jaw position value
    UPROPERTY()
    FVector JawValue = FVector::ZeroVector;
    
    // Funnel values
    UPROPERTY()
    float FunnelRightUp = 0.0f;
    
    UPROPERTY()
    float FunnelRightDown = 0.0f;
    
    UPROPERTY()
    float FunnelLeftUp = 0.0f;
    
    UPROPERTY()
    float FunnelLeftDown = 0.0f;
    
    // Purse values
    UPROPERTY()
    float PurseRightUp = 0.0f;
    
    UPROPERTY()
    float PurseRightDown = 0.0f;
    
    UPROPERTY()
    float PurseLeftUp = 0.0f;
    
    UPROPERTY()
    float PurseLeftDown = 0.0f;
    
    // Corner pull values
    UPROPERTY()
    float CornerPullRight = 0.0f;
    
    UPROPERTY()
    float CornerPullLeft = 0.0f;
    
    // Teeth values
    UPROPERTY()
    FVector TeethUpperValue = FVector::ZeroVector;
    
    UPROPERTY()
    FVector TeethLowerValue = FVector::ZeroVector;
    
    // Tongue values
    UPROPERTY()
    FVector TongueValue = FVector::ZeroVector;
    
    UPROPERTY()
    float TongueInOut = 0.0f;
    
    // Press values
    UPROPERTY()
    float PressRightUp = 0.0f;
    
    UPROPERTY()
    float PressRightDown = 0.0f;
    
    UPROPERTY()
    float PressLeftUp = 0.0f;
    
    UPROPERTY()
    float PressLeftDown = 0.0f;
    
    // Towards values
    UPROPERTY()
    float TowardsRightUp = 0.0f;
    
    UPROPERTY()
    float TowardsRightDown = 0.0f;
    
    UPROPERTY()
    float TowardsLeftUp = 0.0f;
    
    UPROPERTY()
    float TowardsLeftDown = 0.0f;
};

/**
 * Animation class that handles facial movement using data from a JSON file
 */
UCLASS()
class FINAL_DOCTOR_API UMyClass : public UAnimInstance
{
    GENERATED_BODY()
    
public:
    // Called when animation is initialized
    virtual void NativeInitializeAnimation() override;
    
    // Called every frame to update animation
    virtual void NativeUpdateAnimation(float DeltaSeconds) override;
    
    // Value used to drive jaw bone animation
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    FVector JawOpenValue;
    
    // Funnel values
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float FunnelRightUp;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float FunnelRightDown;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float FunnelLeftUp;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float FunnelLeftDown;
    
    // Purse values
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float PurseRightUp;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float PurseRightDown;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float PurseLeftUp;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float PurseLeftDown;
    
    // Corner pull values
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float CornerPullRight;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float CornerPullLeft;
    
    // Teeth values
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    FVector TeethUpperValue;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    FVector TeethLowerValue;
    
    // Tongue values
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    FVector TongueValue;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float TongueInOut;
    
    // Press values
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float PressRightUp;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float PressRightDown;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float PressLeftUp;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float PressLeftDown;
    
    // Towards values
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float TowardsRightUp;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float TowardsRightDown;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float TowardsLeftUp;
    
    UPROPERTY(BlueprintReadOnly, Category = "Animation")
    float TowardsLeftDown;
    
    // Path to the JSON file containing animation data
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
    FString JsonFilePath = "/Users/hassanali/Desktop/talking metahuman/facial_keyframes.json";
    
    // Server polling interval in seconds
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Server")
    float PollInterval = 0.1f;
    
    // Server URL
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Server")
    FString ServerURL = "http://127.0.0.1:5050/start_animation";
    
private:
    // Track elapsed time
    float ElapsedTime;
    
    // Array of keyframes loaded from JSON
    TArray<FJawKeyframe> JawKeyframes;
    
    // Server communication
    void CheckServer();
    void OnServerResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
    
    float LastPollTime;
    bool bUseJsonAnimation;
    
    // Flag to track if animation has completed and needs a new request
    bool bAnimationCompleted;
    
    // Load jaw animation data from JSON file
    void LoadJawAnimationData();
    
    // Reset all animation values to zero
    void ResetAnimationValues();
};
