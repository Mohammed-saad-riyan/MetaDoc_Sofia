// File: MyClass.h
#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Http.h"
#include "MyClass.generated.h"

// Structure to hold a keyframe for facial animation
USTRUCT(BlueprintType)
struct FJawKeyframe
{
    GENERATED_BODY()

    UPROPERTY() float Time = 0.0f;
    UPROPERTY() FVector JawValue = FVector::ZeroVector;
    UPROPERTY() float FunnelRightUp = 0.0f;
    UPROPERTY() float FunnelRightDown = 0.0f;
    UPROPERTY() float FunnelLeftUp = 0.0f;
    UPROPERTY() float FunnelLeftDown = 0.0f;
    UPROPERTY() float PurseRightUp = 0.0f;
    UPROPERTY() float PurseRightDown = 0.0f;
    UPROPERTY() float PurseLeftUp = 0.0f;
    UPROPERTY() float PurseLeftDown = 0.0f;
    UPROPERTY() float CornerPullRight = 0.0f;
    UPROPERTY() float CornerPullLeft = 0.0f;
    UPROPERTY() FVector TeethUpperValue = FVector::ZeroVector;
    UPROPERTY() FVector TeethLowerValue = FVector::ZeroVector;
    UPROPERTY() FVector TongueValue = FVector::ZeroVector;
    UPROPERTY() float TongueInOut = 0.0f;
    UPROPERTY() float PressRightUp = 0.0f;
    UPROPERTY() float PressRightDown = 0.0f;
    UPROPERTY() float PressLeftUp = 0.0f;
    UPROPERTY() float PressLeftDown = 0.0f;
    UPROPERTY() float TowardsRightUp = 0.0f;
    UPROPERTY() float TowardsRightDown = 0.0f;
    UPROPERTY() float TowardsLeftUp = 0.0f;
    UPROPERTY() float TowardsLeftDown = 0.0f;
};

UCLASS()
class MYPROJECT2_API UMyClass : public UAnimInstance
{
    GENERATED_BODY()

public:
    virtual void NativeInitializeAnimation() override;
    virtual void NativeUpdateAnimation(float DeltaSeconds) override;

    UPROPERTY(BlueprintReadOnly, Category = "Animation") FVector JawOpenValue;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float FunnelRightUp;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float FunnelRightDown;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float FunnelLeftUp;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float FunnelLeftDown;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float PurseRightUp;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float PurseRightDown;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float PurseLeftUp;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float PurseLeftDown;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float CornerPullRight;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float CornerPullLeft;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") FVector TeethUpperValue;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") FVector TeethLowerValue;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") FVector TongueValue;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float TongueInOut;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float PressRightUp;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float PressRightDown;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float PressLeftUp;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float PressLeftDown;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float TowardsRightUp;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float TowardsRightDown;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float TowardsLeftUp;
    UPROPERTY(BlueprintReadOnly, Category = "Animation") float TowardsLeftDown;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation") FString JsonFilePath = "/Users/mohammedriyan/Desktop/sofia_server/output/response_keyframes.json";
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Server") float PollInterval = 0.1f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Server") FString ServerURL = "http://127.0.0.1:5050/start_animation";

private:
    float ElapsedTime = 0.0f;
    float LastPollTime = 0.0f;
    bool bUseJsonAnimation = false;
    bool bAnimationCompleted = false;
    bool bJsonHasSpeechEndTime = false;
    float JsonSpeechEndTime = 0.0f;

    TArray<FJawKeyframe> JawKeyframes;

    void CheckServer();
    void OnServerResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
    void LoadJawAnimationData();
    void ResetAnimationValues();
};
