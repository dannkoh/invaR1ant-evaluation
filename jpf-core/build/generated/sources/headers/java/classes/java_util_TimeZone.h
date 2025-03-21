/* DO NOT EDIT THIS FILE - it is machine generated */
#include <jni.h>
/* Header for class java_util_TimeZone */

#ifndef _Included_java_util_TimeZone
#define _Included_java_util_TimeZone
#ifdef __cplusplus
extern "C" {
#endif
#undef java_util_TimeZone_serialVersionUID
#define java_util_TimeZone_serialVersionUID 1LL
#undef java_util_TimeZone_SHORT
#define java_util_TimeZone_SHORT 0L
#undef java_util_TimeZone_LONG
#define java_util_TimeZone_LONG 1L
/*
 * Class:     java_util_TimeZone
 * Method:    createDefaultZone
 * Signature: ()Ljava/util/TimeZone;
 */
JNIEXPORT jobject JNICALL Java_java_util_TimeZone_createDefaultZone
  (JNIEnv *, jclass);

/*
 * Class:     java_util_TimeZone
 * Method:    getTimeZone
 * Signature: (Ljava/lang/String;)Ljava/util/TimeZone;
 */
JNIEXPORT jobject JNICALL Java_java_util_TimeZone_getTimeZone
  (JNIEnv *, jclass, jstring);

/*
 * Class:     java_util_TimeZone
 * Method:    setDefaultValues
 * Signature: (Ljava/util/TimeZone;)V
 */
JNIEXPORT void JNICALL Java_java_util_TimeZone_setDefaultValues
  (JNIEnv *, jclass, jobject);

/*
 * Class:     java_util_TimeZone
 * Method:    getAvailableIDs
 * Signature: ()[Ljava/lang/String;
 */
JNIEXPORT jobjectArray JNICALL Java_java_util_TimeZone_getAvailableIDs__
  (JNIEnv *, jclass);

/*
 * Class:     java_util_TimeZone
 * Method:    getAvailableIDs
 * Signature: (I)[Ljava/lang/String;
 */
JNIEXPORT jobjectArray JNICALL Java_java_util_TimeZone_getAvailableIDs__I
  (JNIEnv *, jclass, jint);

/*
 * Class:     java_util_TimeZone
 * Method:    setID
 * Signature: (Ljava/lang/String;)V
 */
JNIEXPORT void JNICALL Java_java_util_TimeZone_setID
  (JNIEnv *, jobject, jstring);

/*
 * Class:     java_util_TimeZone
 * Method:    getOffset
 * Signature: (IIIIII)I
 */
JNIEXPORT jint JNICALL Java_java_util_TimeZone_getOffset__IIIIII
  (JNIEnv *, jobject, jint, jint, jint, jint, jint, jint);

/*
 * Class:     java_util_TimeZone
 * Method:    getOffset
 * Signature: (J)I
 */
JNIEXPORT jint JNICALL Java_java_util_TimeZone_getOffset__J
  (JNIEnv *, jobject, jlong);

/*
 * Class:     java_util_TimeZone
 * Method:    getOffsets
 * Signature: (J[I)I
 */
JNIEXPORT jint JNICALL Java_java_util_TimeZone_getOffsets
  (JNIEnv *, jobject, jlong, jintArray);

/*
 * Class:     java_util_TimeZone
 * Method:    inDaylightTime
 * Signature: (J)Z
 */
JNIEXPORT jboolean JNICALL Java_java_util_TimeZone_inDaylightTime
  (JNIEnv *, jobject, jlong);

/*
 * Class:     java_util_TimeZone
 * Method:    useDaylightTime
 * Signature: ()Z
 */
JNIEXPORT jboolean JNICALL Java_java_util_TimeZone_useDaylightTime
  (JNIEnv *, jobject);

/*
 * Class:     java_util_TimeZone
 * Method:    observesDaylightTime
 * Signature: ()Z
 */
JNIEXPORT jboolean JNICALL Java_java_util_TimeZone_observesDaylightTime
  (JNIEnv *, jobject);

/*
 * Class:     java_util_TimeZone
 * Method:    getDSTSavings
 * Signature: ()I
 */
JNIEXPORT jint JNICALL Java_java_util_TimeZone_getDSTSavings
  (JNIEnv *, jobject);

/*
 * Class:     java_util_TimeZone
 * Method:    getDisplayName
 * Signature: (ZILjava/util/Locale;)Ljava/lang/String;
 */
JNIEXPORT jstring JNICALL Java_java_util_TimeZone_getDisplayName
  (JNIEnv *, jobject, jboolean, jint, jobject);

#ifdef __cplusplus
}
#endif
#endif
