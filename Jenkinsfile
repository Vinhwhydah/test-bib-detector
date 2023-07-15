def FULL_PATH
def GKE_NAMESPACE
pipeline {
  environment {
    // github
    REPO_NAME = "bib-detector"
    // google cloud artifact repo
    ARTIFACT_REGION = "asia-southeast1-docker.pkg.dev"
    ARTIFACT_PRJ = "system-dev-3749090"
    ARTIFACT_REPO = "bib-wizards-dev"
    ARTIFACT_IMG = "test-bib-detector"
    // gke
    GKE_PRJ = "bib-wizards-dev"
    GKE_REGION = "asia_southeast1"
    GKE_CLUSTER = "bib-staging-dev"
    GKE_POD = "detector"
    GKE_CONTAINER = "detector"
  }
  agent {
    kubernetes {
      yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    some-label: dind-agent
spec:
  serviceAccountName: jenkins-admin
  dnsConfig:
    namesevers:
      - 8.8.8.8
  containers:
  - name: dind
    image: docker:latest
    imagePullPolicy: Always
    tty: true
    securityContext:
      privileged: true
    volumeMounts:
      - name: docker-graph-storage
        mountPath: /var/lib/docker
  - name: trivy
    image: bitnami/trivy
    command: ["sleep"]
    args: ["99999d"]
    tty: true
    securityContext:
      runAsUser: 0  
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run/docker.sock
  - name: helm
    image: alpine/helm
    imagePullPolicy: Always
    tty: true
    command: ["cat"]
    securityContext:
      runAsUser: 0
  - name: kubectl
    image: bitnami/kubectl:latest
    command:
    - cat
    tty: true
    securityContext:
      runAsUser: 0
    volumes:
    - name: docker-sock
      hostPath:
        path: /var/run/docker.sock
  volumes:
    - name: docker-graph-storage
      emptyDir: {}
    - name: docker-sock
      hostPath:
        path: /var/run/docker.sock
"""
    }
  }
  stages {
    stage('Git Pull') {
        steps {
            script {
                container('dind') {
                  // // The below will clone your repo and will be checked out to master branch by default.
                  // def scmVars = checkout([
                  // 								$class: 'GitSCM',
                  // 								branches: [[name: "*/${env.BRANCH_NAME}"]],
                  // 								doGenerateSubmoduleConfigurations: false,
                  // 								userRemoteConfigs: [[credentialsId: '4915da52-49df-42ea-843b-2f3412a28b16', url: "git@github.com:kyokai-lab/${env.REPO_NAME}.git"]]
                  // 							])
                  // // assign git_commit
                  // env.GIT_COMMIT = scmVars.GIT_COMMIT
                  env.BRANCH_NAME = scm.branches[0].name
                  if (env.BRANCH_NAME == "main") {
                    GKE_NAMESPACE = "dev"
                  }
                  else if (env.BRANCH_NAME == "production") {
                    GKE_NAMESPACE = "prod"
                  }
                  else if (env.BRANCH_NAME == "staging") {
                    GKE_NAMESPACE = "staging"
                  }
                  else {
                    GKE_NAMESPACE = "default"
                  }
                }
            }
        }
    }
    stage('Prepare') {
      steps {
        container('dind') {
          configFileProvider([configFile(fileId: "${env.REPO_NAME}-${env.BRANCH_NAME}-env", targetLocation:".env")]) {
            sh "cat .env"
          }
          configFileProvider([configFile(fileId: "${env.REPO_NAME}-${env.BRANCH_NAME}-creds", targetLocation:"bib_detector_credential.json")]) {
            sh "cat bib_detector_credential.json"
          }
        }
      }
    }
    stage('Build') {
      steps {
        container('dind') {
          script {
            FULL_PATH = "${env.ARTIFACT_REGION}/${env.ARTIFACT_PRJ}/${env.ARTIFACT_REPO}/${env.ARTIFACT_IMG}:${env.GIT_COMMIT}-${env.BUILD_NUMBER}"
            sh "ls -a"
            // sh "docker build --network host -t ${FULL_PATH} ."
          }
        }
      }
    }
    stage('Push') {
      steps {
        container('dind') {
          withCredentials([file(credentialsId: 'whydah-sys-gcr-creds', variable: 'GC_KEY')]){
            sh 'docker login -u _json_key --password-stdin https://$ARTIFACT_REGION < $GC_KEY'
          }
          // sh "docker push ${FULL_PATH}"
        }
      }
    }
    stage('Connect Cluster And Deploy'){
      steps {
        container('kubectl'){
          script {
            withCredentials([file(credentialsId: "${env.GKE_PRJ}-kubectl", targetLocation: 'TMPKUBECONFIG')]) {
              sh "${TMPKUBECONFIG}"
              sh "kubectl config set-context gke_${env.GKE_PRJ}_${env.GKE_REGION}_${env.GKE_CLUSTER}_${env.GKE_NAMESPACE} --user=jenkins --cluster=gke_${env.GKE_PRJ}_${env.GKE_REGION}_${env.GKE_CLUSTER} --namespace=${GKE_NAMESPACE}"
              sh "kubectl config use-context gke_${env.GKE_PRJ}_${env.GKE_REGION}_${env.GKE_CLUSTER}_${env.GKE_NAMESPACE}"
              sh "kubectl get pods"
              sh "kubectl set image deployment --namespace=${GKE_NAMESPACE} ${env.GKE_POD} ${env.GKE_CONTAINER}=${FULL_PATH}"
            }
          }
        }
      }
    }
// 		stage('Deploy') {
// 			steps {
// 				container('dind') {
// 					script {
// 					withCredentials([sshUserPrivateKey(credentialsId: 'devs', keyFileVariable: 'identity', passphraseVariable: 'passPhrase', usernameVariable: 'userName')]) {
// 						def remote = [:]
// 						remote.name = 'devs'
// 						remote.host = '10.1.1.52'
// 						remote.allowAnyHosts = true
// 						remote.user = userName
// 						remote.identityFile = identity
// 						remote.passphrase = passPhrase

// 						writeFile file: 'set_image.sh', text: """
// #!/bin/bash
// kubectl config use-context gke_bib-wizards-dev_asia-southeast1_bib-dev-staging
// kubectl config current-context
// kubectl set image deployment --namespace=staging detector detector=asia-southeast1-docker.pkg.dev/system-dev-3749090/bib-wizards-dev/test-bib-detector:${env.GIT_COMMIT}-${env.BUILD_NUMBER}"""
// 						sshPut remote: remote, from: 'set_image.sh', into: '.'
// 						sshScript remote: remote, script: "set_image.sh"
// 						// sshCommand remote: remote, command: "sh set_image.sh"
// 						}
// 					}
// 				}
// 			}
// 		}
  }

  post {
    success {
      echo 'Pulish a tag here'
    }

    unsuccessful {
      echo 'Notify GoogleChat channel'
    }
  }

}
